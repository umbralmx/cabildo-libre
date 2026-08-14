#!/usr/bin/env python3
"""Puerta de calidad — comprueba que lo que se va a publicar sea real.

El proyecto ya declara su procedencia con rigor: cada sección lleva su
`cobertura`, `no_determinable` es un valor y no un cero silencioso, los nombres
que no casan con el roster se reportan en vez de forzarse. Lo que faltaba es la
otra mitad: **nada preguntaba si una cifra significa lo que dice su etiqueta.**

Tres cosas que pasaron por no tenerlo, todas publicadas y ninguna detectada por
las declaraciones de cobertura:

- El acta 17 declaró durante semanas un monto de **$4,009,960,066**. El OCR sólo
  contiene `1,009,960,065.66`, seis veces, y el `4,009,960,066` cero veces. La
  cifra tenía procedencia perfecta —punto, acta, categoría— y era inventada.
- El lote del 2026-08-14 dejó **5 ventanas de lectura fallidas** en 4 actas. La
  profundidad de lectura cayó de 100 % a 98.09 % y el panel lo declaró
  correctamente; nadie lo miró.
- Ese mismo lote movió la suma de dinero declarado de **$13.2 mil millones a
  $17.1 mil millones**. Ningún umbral se disparó porque no había ninguno.

Cada comprobación es barata: lee lo ya generado, no llama a ningún modelo y
corre en segundos. Se ejecuta **después** de commitear el lote y **antes** de
publicar, para que un lote caro no se pierda pero tampoco se despliegue con
números que nadie revisó.

Severidades:
  ERROR  — bloquea la publicación. Algo publicado sería falso o incompleto.
  AVISO  — se reporta y no bloquea. Necesita criterio humano, no corrección.

Uso:
    python3 processor/verificar.py
    python3 processor/verificar.py --actualizar-linea-base   # aceptar cifras nuevas
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACTAS_JSON = ROOT / "data" / "actas.json"
OCR_DIR = ROOT / "data" / "ocr"
SUMMARY_DIR = ROOT / "data" / "summaries"
SITE_DIR = ROOT / "site"
LINEA_BASE = ROOT / "data" / "linea-base.json"

# Cuánto puede moverse una cifra agregada entre lotes sin que alguien lo confirme.
# El re-resumen no es determinista —la bitácora mide ~1 % de puntos que se mueven
# en ambas direcciones sin cambiar una línea de código— así que el umbral tiene
# que tolerar eso y detenerse muy por debajo de un salto como el del 2026-08-14.
TOLERANCIA = 0.03


class Hallazgo:
    def __init__(self, check: str, severidad: str, mensaje: str, detalle: list[str] | None = None):
        self.check = check
        self.severidad = severidad
        self.mensaje = mensaje
        self.detalle = detalle or []


def _json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _solo_digitos(s: str) -> str:
    return re.sub(r"\D", "", s)


# ── 1. ¿Cada monto existe en el acta que dice citarlo? ───────────────────────

def montos_en_fuente() -> list[Hallazgo]:
    """La comprobación insignia: una cifra que no está en el OCR es inventada.

    Se compara contra el OCR reducido a sólo dígitos, lo que hace la prueba
    **conservadora a propósito**: ignora cómo el escáner rompió los separadores
    (`121.800,000.00`, `53,312446.10`) y sólo falla cuando la secuencia de
    dígitos no aparece en ninguna parte del acta. Un falso positivo aquí sería
    ruido; lo que se persigue es que no haya falsos negativos.
    """
    faltantes: list[str] = []
    revisados = 0
    for p in sorted(SUMMARY_DIR.glob("*.json")):
        ocr_p = OCR_DIR / p.name
        if not ocr_p.exists():
            continue
        digitos = _solo_digitos(_json(ocr_p).get("texto_completo", ""))
        d = _json(p)
        for pt in d.get("puntos", []):
            for m in pt.get("montos") or []:
                if not isinstance(m.get("valor_mxn"), (int, float)):
                    continue
                revisados += 1
                texto = m.get("texto") or ""
                nums = re.findall(r"\d[\d,\.\s]*\d|\d", texto)
                if not nums:
                    continue
                # La cifra larga es la del monto; las cortas suelen ser fechas,
                # números de oficio o el numeral del punto.
                cifra = _solo_digitos(max(nums, key=len))
                if len(cifra) < 4:
                    continue
                if cifra not in digitos:
                    faltantes.append(
                        f"acta {d.get('no_acta')} punto {pt['n']}: «{texto[:60]}» "
                        f"→ {m['valor_mxn']:,.2f} no aparece en el OCR del acta")
    if faltantes:
        return [Hallazgo("montos_en_fuente", "ERROR",
                         f"{len(faltantes)} de {revisados} montos citan una cifra que su acta "
                         f"no contiene", faltantes)]
    return [Hallazgo("montos_en_fuente", "OK", f"{revisados} montos, todos presentes en su acta")]


# ── 2. ¿Se leyó el acta entera? ─────────────────────────────────────────────

def lectura_completa() -> list[Hallazgo]:
    """Una ventana fallida es texto que nadie leyó y que nadie va a echar de menos.

    Es error y no aviso justamente porque el sistema *sí* lo declara con
    honestidad: el panel bajó a 98.09 % y siguió pareciendo normal. Repararlo es
    volver a correr las actas afectadas, que cuesta centavos.
    """
    rotas: list[str] = []
    for p in sorted(SUMMARY_DIR.glob("*.json"), key=lambda x: x.stem):
        lec = _json(p).get("lectura") or {}
        fallidas = lec.get("ventanas_fallidas") or 0
        if fallidas:
            rotas.append(f"acta {p.stem.split('-')[-1]}: {fallidas} de "
                         f"{lec.get('ventanas', '?')} ventanas fallidas")
    if rotas:
        return [Hallazgo("lectura_completa", "ERROR",
                         f"{len(rotas)} acta(s) se resumieron con ventanas fallidas — "
                         f"su texto no se leyó entero", rotas)]
    return [Hallazgo("lectura_completa", "OK", "todas las actas se leyeron enteras")]


# ── 3. ¿Quedan puntos donde dos lecturas se contradicen? ─────────────────────

def sin_conflictos(analytics: dict) -> list[Hallazgo]:
    conf = (analytics.get("lectura") or {}).get("puntos_en_conflicto") or []
    if conf:
        return [Hallazgo("sin_conflictos", "ERROR",
                         f"{len(conf)} punto(s) donde dos ventanas declararon resultados "
                         f"distintos", [f"acta {c.get('no_acta')} punto {c.get('punto')}" for c in conf])]
    return [Hallazgo("sin_conflictos", "OK", "ningún punto en conflicto")]


# ── 4. ¿La cobertura declarada corresponde a los datos? ──────────────────────

def cobertura_al_dia(analytics: dict) -> list[Hallazgo]:
    """El error de las «74 sesiones»: una cifra correcta que dejó de serlo.

    El término creció de 74 a 78 actas y el panel siguió diciendo 74 durante
    semanas. Aquí no se comprueba prosa —eso ya se resolvió leyendo del JSON—
    sino que el propio agregado no se haya quedado atrás de `actas.json`.
    """
    termino = analytics.get("termino")
    reales = sum(1 for a in _json(ACTAS_JSON)["actas"] if a.get("periodo") == termino)
    declaradas = (analytics.get("cobertura") or {}).get("actas_en_termino")
    if declaradas != reales:
        return [Hallazgo("cobertura_al_dia", "ERROR",
                         f"el agregado declara {declaradas} actas en {termino} y actas.json "
                         f"tiene {reales}: hay que reconstruir la analítica")]
    return [Hallazgo("cobertura_al_dia", "OK", f"{reales} actas en {termino}, coincide")]


# ── 5. Montos que huelen a doble conteo ─────────────────────────────────────

def montos_no_aditivos() -> list[Hallazgo]:
    """Generaliza el guard de *total + desglose* a los casos que hoy se le escapan.

    `_suma_punto` en `build_analytics.py` sólo actúa cuando el punto lista cinco
    montos o más. El acta 17 punto 7 lista **tres** y es el caso más claro que
    tenemos de cifras que no se pueden sumar:

        «una Ley de Ingresos recaudada por el orden de los $937 millones […] y un
        Presupuesto de Egresos Ejercido de 971 millones existiendo un desfase de
        más de 34 millones»

    Ingreso, gasto y la diferencia entre ambos. Sumarlos da $1.94 mil millones de
    «dinero declarado» que no corresponde a ninguna decisión. La forma es
    detectable sin entender el texto: **un monto que iguala la suma de los
    demás**. Se reporta como aviso porque qué hacer con ello —excluirlo, marcarlo,
    reformular el indicador— es una decisión editorial, no una corrección.
    """
    sospechosos: list[str] = []
    for p in sorted(SUMMARY_DIR.glob("*.json")):
        d = _json(p)
        for pt in d.get("puntos", []):
            vals = [m["valor_mxn"] for m in (pt.get("montos") or [])
                    if isinstance(m.get("valor_mxn"), (int, float))]
            # 5 o más ya lo cubre `_suma_punto`; aquí interesan los que se le escapan.
            if not 2 <= len(vals) <= 4:
                continue
            mayor = max(vals)
            resto = sum(vals) - mayor
            if resto and abs(mayor - resto) / mayor < 0.02:
                sospechosos.append(
                    f"acta {d.get('no_acta')} punto {pt['n']}: {mayor:,.0f} ≈ suma de los otros "
                    f"{len(vals) - 1} ({resto:,.0f}) — se están sumando los dos")
    if sospechosos:
        return [Hallazgo("montos_no_aditivos", "AVISO",
                         f"{len(sospechosos)} punto(s) donde un monto iguala la suma de los "
                         f"demás y el guard de total+desglose no alcanza", sospechosos)]
    return [Hallazgo("montos_no_aditivos", "OK", "ningún punto con la forma total+desglose sin guardar")]


# ── 6. ¿De dónde sale el dinero que se publica? ─────────────────────────────

def concentracion_del_dinero(analytics: dict) -> list[Hallazgo]:
    """Si una sola categoría domina la suma, la suma no mide lo que su rótulo dice.

    Hoy el 93.6 % del total declarado sale de `presupuesto_finanzas`, que son en
    su mayoría **informes de cuenta pública**: cifras que el cabildo discute, no
    dinero que aprueba. El rótulo del panel («Suma de lo declarado en las actas
    leídas») es cierto y aun así se lee como si fuera gasto autorizado.
    """
    por_cat: dict[str, float] = {}
    total = 0.0
    for p in sorted(SUMMARY_DIR.glob("*.json")):
        for pt in _json(p).get("puntos", []):
            vals = [m["valor_mxn"] for m in (pt.get("montos") or [])
                    if isinstance(m.get("valor_mxn"), (int, float))]
            if not vals:
                continue
            s = float(sum(vals))
            cat = pt.get("categoria") or "—"
            por_cat[cat] = por_cat.get(cat, 0.0) + s
            total += s
    if not total:
        return [Hallazgo("concentracion_del_dinero", "OK", "sin montos que agregar")]
    cat, val = max(por_cat.items(), key=lambda kv: kv[1])
    cuota = val / total
    if cuota > 0.5:
        return [Hallazgo("concentracion_del_dinero", "AVISO",
                         f"el {cuota:.1%} del dinero declarado sale de una sola categoría "
                         f"({cat}) — la suma describe esa categoría, no al cabildo",
                         [f"{c}: {v:,.0f} ({v/total:.1%})"
                          for c, v in sorted(por_cat.items(), key=lambda kv: -kv[1])[:5]])]
    return [Hallazgo("concentracion_del_dinero", "OK",
                     f"la categoría mayor ({cat}) aporta {cuota:.1%} del total")]


# ── 7. ¿El índice de búsqueda propone todas las actas que debería? ──────────

def indice_completo() -> list[Hallazgo]:
    """La invariante que sostiene que la búsqueda no cambió de resultados.

    `site/fulltext-index.json` acota las candidatas y el regex de `app.js` decide,
    así que una candidata de más es inofensiva —el regex la descarta— y el único
    fallo posible es una **de menos**: un acta que coincide y que el índice no
    propuso. Eso sólo ocurre si al índice le falta un posting.

    Aquí se vuelve a tokenizar cada acta desde `data/ocr/` con el mismo `fold` y
    la misma expresión que construyeron el índice, y se comprueba que cada token
    apunte de vuelta a su acta. Si esto pasa, no hay falsos negativos posibles y
    los resultados son idénticos a los del `fulltext.json` monolítico.

    Se comprueba en Python y no con el JS real a propósito: el proyecto tiene que
    seguir corriendo sin cadena de herramientas (`CLAUDE.md` — *boring, static, zero
    ops*), y esta invariante es más fuerte que un puñado de consultas de ejemplo.
    """
    idx_p = SITE_DIR / "fulltext-index.json"
    ft_dir = SITE_DIR / "fulltext"
    if not idx_p.exists():
        return [Hallazgo("indice_completo", "ERROR",
                         "falta site/fulltext-index.json — corre build_site_index.py")]

    from build_site_index import tokens_de  # mismo fold y misma tokenización

    idx = _json(idx_p)
    actas = idx.get("actas") or []
    tokens = idx.get("tokens") or {}
    posicion = {a: i for i, a in enumerate(actas)}

    problemas: list[str] = []
    ocr_ids = {p.stem for p in OCR_DIR.glob("*.json")}
    if set(actas) != ocr_ids:
        faltan = sorted(ocr_ids - set(actas))[:5]
        sobran = sorted(set(actas) - ocr_ids)[:5]
        problemas.append(f"el índice cubre {len(actas)} actas y hay {len(ocr_ids)} con OCR"
                         + (f"; faltan {faltan}" if faltan else "")
                         + (f"; sobran {sobran}" if sobran else ""))

    sin_archivo = [a for a in actas if not (ft_dir / f"{a}.json").exists()]
    if sin_archivo:
        problemas.append(f"{len(sin_archivo)} acta(s) en el índice sin su archivo en "
                         f"site/fulltext/: {sin_archivo[:5]}")

    postings_faltantes = 0
    for acta_id in actas:
        f = ft_dir / f"{acta_id}.json"
        if not f.exists():
            continue
        i = posicion[acta_id]
        for tok in tokens_de(_json(f).get("texto", "")):
            if i not in (tokens.get(tok) or ()):
                postings_faltantes += 1
                if postings_faltantes <= 5:
                    problemas.append(f"acta {acta_id}: el token «{tok}» está en su texto y "
                                     f"no en el índice")
    if postings_faltantes > 5:
        problemas.append(f"… y {postings_faltantes - 5} posting(s) más ausentes")

    if problemas:
        return [Hallazgo("indice_completo", "ERROR",
                         "el índice de búsqueda no cubre todo su texto: hay consultas que "
                         "perderían resultados en silencio", problemas)]
    return [Hallazgo("indice_completo", "OK",
                     f"{len(tokens):,} tokens sobre {len(actas)} actas, sin postings ausentes")]


# ── 8. Línea base: ¿algo se movió sin que nadie lo confirmara? ───────────────

def _cifras_vigiladas(a: dict) -> dict:
    dec = a.get("decisiones") or {}
    mon = a.get("montos") or {}
    lec = a.get("lectura") or {}
    cob = a.get("cobertura") or {}
    cifras = {
        "cobertura.actas_en_termino": cob.get("actas_en_termino"),
        "cobertura.con_resumen": cob.get("con_resumen"),
        "decisiones.n_puntos": dec.get("n_puntos"),
        "decisiones.n_sustantivos": dec.get("n_sustantivos"),
        "montos.n_con_valor": mon.get("n_con_valor"),
        "montos.suma_bruta_mxn": mon.get("suma_bruta_mxn"),
        "montos.suma_declarada_mxn": mon.get("suma_declarada_mxn"),
        "lectura.proporcion": lec.get("proporcion"),
    }
    for k, v in (dec.get("por_sentido") or {}).items():
        cifras[f"decisiones.por_sentido.{k}"] = v
    return {k: v for k, v in cifras.items() if isinstance(v, (int, float))}


def linea_base(analytics: dict, actualizar: bool, hay_errores: bool) -> list[Hallazgo]:
    """Lo que faltaba el 2026-08-14: un umbral que se queje solo.

    El re-resumen no es reproducible al 100 %, así que la línea base no exige
    igualdad: exige que nadie mueva una cifra publicada más de `TOLERANCIA` sin
    decirlo. Aceptar un cambio es explícito (`--actualizar-linea-base`), que es
    justamente el momento en que alguien mira los números.
    """
    actuales = _cifras_vigiladas(analytics)
    existia = LINEA_BASE.exists()

    # Fijar la referencia sobre datos que ya fallaron una comprobación la
    # convertiría en la memoria de un estado malo, y los lotes siguientes se
    # medirían contra él sin quejarse.
    if not existia and hay_errores and not actualizar:
        return [Hallazgo("linea_base", "AVISO",
                         "no se fija línea base: hay errores sin resolver y quedaría "
                         "anclada a ellos. Se creará en la primera corrida limpia")]

    if actualizar or not existia:
        LINEA_BASE.write_text(
            json.dumps({"termino": analytics.get("termino"),
                        "generado": analytics.get("generado"),
                        "cifras": actuales}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        return [Hallazgo("linea_base", "OK",
                         f"línea base {'actualizada' if existia else 'creada'} con "
                         f"{len(actuales)} cifras ({LINEA_BASE.relative_to(ROOT)})")]

    previas = (_json(LINEA_BASE).get("cifras") or {})
    movidas: list[str] = []
    for k, ahora in actuales.items():
        antes = previas.get(k)
        if not isinstance(antes, (int, float)):
            movidas.append(f"{k}: cifra nueva ({ahora:,.2f}), sin línea base")
            continue
        if antes == 0:
            if ahora != 0:
                movidas.append(f"{k}: 0 → {ahora:,.2f}")
            continue
        delta = abs(ahora - antes) / abs(antes)
        if delta > TOLERANCIA:
            movidas.append(f"{k}: {antes:,.2f} → {ahora:,.2f} ({(ahora-antes)/abs(antes):+.1%})")
    if movidas:
        return [Hallazgo("linea_base", "ERROR",
                         f"{len(movidas)} cifra(s) publicadas se movieron más de "
                         f"{TOLERANCIA:.0%} — confirma y corre con --actualizar-linea-base",
                         movidas)]
    return [Hallazgo("linea_base", "OK", f"{len(actuales)} cifras dentro de ±{TOLERANCIA:.0%}")]


# ── 8. Nombres que el acta menciona y el roster no reconoce ─────────────────

def nombres_sin_mapear(analytics: dict) -> list[Hallazgo]:
    """Informativo por diseño: un nombre sin mapear suele ser una suplencia real.

    No es un error que corregir — es el hallazgo que produjo el caso de la
    suplente del acta 52. Se reporta para que no desaparezca de la vista.
    """
    sm = (analytics.get("registro_voto") or {}).get("nombres_sin_mapear") or []
    if sm:
        nombres = [f"{s['nombre']} ({s.get('menciones', '?')} mención/es)"
                   if isinstance(s, dict) else str(s) for s in sm]
        return [Hallazgo("nombres_sin_mapear", "AVISO",
                         f"{len(nombres)} nombre(s) citados por el acta que no están en el roster",
                         nombres)]
    return [Hallazgo("nombres_sin_mapear", "OK", "todos los nombres citados están en el roster")]


# ── ejecución ───────────────────────────────────────────────────────────────

SIMBOLO = {"OK": "  ok  ", "AVISO": " aviso", "ERROR": " ERROR"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--termino", default="2024-2027")
    ap.add_argument("--actualizar-linea-base", action="store_true",
                    help="acepta las cifras actuales como la nueva línea base")
    args = ap.parse_args()

    ruta = SITE_DIR / f"analytics-{args.termino}.json"
    if not ruta.exists():
        print(f"no existe {ruta} — corre antes processor/build_analytics.py", file=sys.stderr)
        return 2
    analytics = _json(ruta)

    hallazgos: list[Hallazgo] = []
    hallazgos += montos_en_fuente()
    hallazgos += lectura_completa()
    hallazgos += sin_conflictos(analytics)
    hallazgos += cobertura_al_dia(analytics)
    hallazgos += montos_no_aditivos()
    hallazgos += concentracion_del_dinero(analytics)
    hallazgos += nombres_sin_mapear(analytics)
    hallazgos += indice_completo()
    # Al final y con el resultado de las demás: la línea base no debe anclarse
    # a un estado que ya falló.
    hallazgos += linea_base(analytics, args.actualizar_linea_base,
                            any(h.severidad == "ERROR" for h in hallazgos))

    print(f"\nVerificación del término {args.termino}\n" + "=" * 68)
    for h in hallazgos:
        print(f"{SIMBOLO[h.severidad]}  {h.check}: {h.mensaje}")
        for d in h.detalle[:12]:
            print(f"          · {d}")
        if len(h.detalle) > 12:
            print(f"          · … y {len(h.detalle) - 12} más")

    errores = [h for h in hallazgos if h.severidad == "ERROR"]
    avisos = [h for h in hallazgos if h.severidad == "AVISO"]
    print("=" * 68)
    print(f"{len(errores)} error(es) · {len(avisos)} aviso(s) · "
          f"{len(hallazgos) - len(errores) - len(avisos)} ok")
    if errores:
        print("\nNo publicar. Los errores significan que algo publicado sería falso o "
              "incompleto;\nlos datos ya commiteados quedan en el repo para inspeccionarlos.")
    return 1 if errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
