#!/usr/bin/env python3
"""Estructura de la sesión, leída del propio acta — sin modelo, sin inferencia.

Estructura dos hechos que el acta declara literalmente y que hasta ahora nadie
recogía:

1. **El tipo de sesión** — `ordinaria`, `extraordinaria` o `solemne`. Está en el
   encabezado ("para celebrar Sesión Ordinaria"). No necesita modelo.

2. **La modificación del órden del día en sesión.** El cabildo retira e incorpora
   asuntos *antes* de votar el órden del día, y después el acta reimprime el
   órden final. Ocurre en 19 de las 78 actas del término.

El punto 2 no es un adorno: **corrige un defecto real de los resúmenes.** El
índice del portal publica el órden del día *previo*, y ése es el que
`summarize_colima.py` entrega al modelo como referencia de numeración. Cuando la
sesión mueve el órden, el cuerpo del acta pasa a numerar por el órden final y las
ventanas de lectura discrepan: una numera como el índice, otra como el acta.
`fusionar_puntos` las une por `n` y termina fundiendo **dos asuntos distintos en
un mismo registro**.

Caso comprobado — acta 48, punto 7. La Síndica retiró el dictamen de ampliaciones
SUPERNUMERARIO-BASE (VII del órden previo) y un regidor incorporó otro asunto al
final. Todo lo posterior recorrió un lugar, así que el VII final son las tres
licencias comerciales. El registro resultante mezcla los dos: la prosa habla del
dictamen retirado, mientras el sentido (`aprobado`), la votación (`unánime`) y la
comisión (*Comercios, Mercados y Restaurantes*) son de las licencias. La ficha se
delata sola: la categoría dice `presupuesto_finanzas` y la comisión es de
comercios. Y como el órden previo y el final tienen aquí **la misma longitud**
—se retiró uno y se incorporó otro—, ningún conteo lo detecta.

**Una petición de retiro puede ser rechazada** (acta 41: el cabildo aprobó retirar
el Séptimo Punto pero *no* aprobó retirar el Sexto). Por eso se transcribe la
petición y, aparte, la constancia de cómo se votó; el resultado sólo se clasifica
cuando el acta lo dice. Suponer que toda petición prosperó movería puntos que
nunca se movieron.

**Verificación cruzada.** La detección se ancla en la fórmula de modificación, y
se contrasta con una señal independiente: el acta que modifica su órden imprime
la lista **tres** veces ("Lista de asistencia" abre cada impresión), y la que no
lo modifica, dos. Las dos señales coinciden en las mismas 19 actas del término,
sin falsos positivos ni negativos. Cuando discrepan, se marca `revisar`.

Este módulo **no repara los resúmenes ya generados ni reordena nada**: marca las
actas donde la numeración del índice dejó de valer y transcribe lo que el acta
dice. Volver a resumirlas es una decisión de costo, y se toma con el dato a la
vista. Regla del proyecto: el hueco se hace visible, no se rellena.

Uso:
    python3 processor/orden_del_dia.py            # escribe data/estructura/<id>.json
    python3 processor/orden_del_dia.py --dry-run  # sólo el resumen de control
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

from limpieza import limpiar

RAIZ = Path(__file__).resolve().parent.parent
DIR_OCR = RAIZ / "data" / "ocr"
DIR_SALIDA = RAIZ / "data" / "estructura"


# --- 1. Tipo de sesión -------------------------------------------------------

# El encabezado dice "...para celebrar Sesión Ordinaria...". Se busca sólo en la
# cabeza del acta: más adelante el texto cita sesiones anteriores de otro tipo
# ("aprobada en la sesión extraordinaria del 29 de mayo") y tomar el tipo de ahí
# etiquetaría mal la sesión presente.
_TIPO_RE = re.compile(r"Sesi[oó]n\s+(Ordinaria|Extraordinaria|Solemne)", re.I)
_CABEZA_CHARS = 6000

# Segunda declaración del propio tipo, en el bloque de firmas: "las presentes
# firmas corresponden al Acta N° 54, de la Sesión Extraordinaria de Cabildo del
# día 27 de noviembre del 2025". Va anclada al número de acta, así que no puede
# confundirse con la cita de otra sesión — y por eso sirve donde el encabezado
# quedó ilegible: en el acta 54 el OCR interleó una columna y partió la palabra
# ("para celebrar Ses | ACTA DE CABILDO | ión Extraordinaria"). Recomponer eso
# sería adivinar; leer la firma no lo es.
_TIPO_FIRMA_RE = re.compile(
    r"Acta\s*N\W{0,4}\s*(\d{1,3})\s*,?\s*de\s+la\s+Sesi[oó]n\s+(Ordinaria|Extraordinaria|Solemne)",
    re.I,
)


def tipo_sesion(texto: str, no_acta: int | None = None) -> dict:
    """El tipo de sesión y de dónde salió.

    Devuelve `{tipo, fuente, concuerdan}`. `tipo` es `ordinaria`,
    `extraordinaria`, `solemne` o `no_determinable`. Manda el encabezado; la
    firma cubre los encabezados que el OCR destruyó. Cuando las dos declaraciones
    existen y **no** coinciden, se conserva la del encabezado y se marca
    `concuerdan: False` para que la discrepancia se vea en lugar de resolverse a
    escondidas.
    """
    m = _TIPO_RE.search(texto[:_CABEZA_CHARS])
    encabezado = m.group(1).lower() if m else None

    firma = None
    for f in _TIPO_FIRMA_RE.finditer(texto):
        if no_acta is None or int(f.group(1)) == no_acta:
            firma = f.group(2).lower()
            break

    tipo = encabezado or firma or "no_determinable"
    fuente = "encabezado" if encabezado else ("firma" if firma else "ninguna")
    return {
        "tipo": tipo,
        "fuente": fuente,
        "concuerdan": None if not (encabezado and firma) else encabezado == firma,
    }


# --- 2. Modificación del órden del día ---------------------------------------

# Ancla principal. El acta cierra la modificación con una de tres fórmulas; el
# OCR destruye "continuación" con frecuencia ("CONtiINUACIÓN", "continua CIÓN",
# y en el acta 47 directamente "CONAN"), así que el ancla NO depende de esa
# palabra.
_MODIF_RE = re.compile(
    r"modificaci\w+\s+al\s+Orden\s+del\s+D[ií]a"
    r"|Orden\s+del\s+D[ií]a\s+con\s+la\s+modificaci\w+"
    r"|con\s+la\s+modificaci\w+\s+autorizada",
    re.I,
)

# Señal independiente: cada impresión del órden del día abre con "Lista de
# asistencia". Dos impresiones = órden intacto; tres = órden reimpreso.
_LISTA_RE = re.compile(r"Lista\s+de\s+asistencia", re.I)

# Peticiones. El verbo y el complemento se separan por hasta cuatro palabras
# ("solicitó se incorpore al Orden del Día", "pidió retirar de Orden del Día").
_PETICION_RE = re.compile(
    r"(retirar|retirara|retire|incorporar|incorpore|adicionar|agregar|agregue)"
    # "del" y "al" son lo normal, pero el OCR y la propia redacción producen
    # "retirar de Orden del Día" (acta 76); exigir la ele perdía esa acta entera.
    r"(?:\s+\w+){0,4}?\s+(?:de|del|al)\s+Orden\s+del\s+D[ií]a",
    re.I,
)
_RETIRO = {"retirar", "retirara", "retire"}

# Ordinal con el que la petición nombra el punto afectado ("el Séptimo Punto").
# Es el dato más preciso que da el acta: dice exactamente dónde empieza el
# corrimiento.
_ORDINALES = {
    "primer": 1, "primero": 1, "segundo": 2, "tercer": 3, "tercero": 3, "cuarto": 4,
    "quinto": 5, "sexto": 6, "septimo": 7, "octavo": 8, "noveno": 9, "decimo": 10,
    "undecimo": 11, "duodecimo": 12,
}
_ORDINAL_RE = re.compile(
    r"\b(?:el\s+)?(decimo\s+)?(" + "|".join(_ORDINALES) + r")\s+punto\b", re.I
)

# Constancia de cómo se votó la modificación.
_UNANIME_RE = re.compile(r"modificaci\w+.{0,160}?por\s+unanimidad", re.I | re.S)
_MAYORIA_RE = re.compile(r"modificaci\w+.{0,200}?(por\s+mayor[ií]a|voto\w*\s+en\s+contra)", re.I | re.S)
_NEGADA_RE = re.compile(r"no\s+aprob\w+\s+(?:retirar|incorporar|el)", re.I)

# Viñetas del OCR: Tesseract lee el bullet redondo como "e", "+", "»" o "*".
_VINETA_RE = re.compile(r"(?:^|\n)\s*(?:[•·+*>»~]|[eoa])\s+(?=[A-ZÁÉÍÓÚÑ])")


def _sin_acentos(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _recorta(t: str) -> str:
    t = re.split(r"\.-|\.\s*\n|\n\s*\n", t.strip(), maxsplit=1)[0]
    return re.sub(r"\s+", " ", t).strip(" .,-–—:=")


def _asunto(despues: str) -> str | None:
    """El asunto que la petición nombra, tal como el acta lo escribe.

    Primero busca una viñeta (la forma más común); si no la hay, toma el texto
    inmediatamente posterior al verbo, que es como lo redactan las actas que
    enuncian el asunto en línea (acta 36).
    """
    partes = _VINETA_RE.split(despues[:1500])
    cand = partes[1] if len(partes) > 1 else despues
    t = _recorta(cand)
    return t if 15 <= len(t) <= 400 else None


def _ordinal(fragmento: str) -> int | None:
    m = _ORDINAL_RE.search(_sin_acentos(fragmento))
    if not m:
        return None
    base = _ORDINALES[m.group(2).lower()]
    return base + 10 if m.group(1) else base


def modificacion(texto: str) -> dict | None:
    """Lo que la sesión cambió de su órden del día, o None si no lo cambió.

    Transcribe las peticiones verbatim y la forma en que se votaron. No
    reconstruye el órden final ítem por ítem: los numerales romanos del OCR están
    demasiado dañados (`L`, `TI.`, `vL`, `xXIIL`) y en varias actas la columna de
    numerales quedó separada de su texto. Reconstruirlos sería adivinar.
    """
    ancla = _MODIF_RE.search(texto)
    reimpresiones = len(_LISTA_RE.findall(texto))
    if not ancla:
        return None

    peticiones = []
    for m in _PETICION_RE.finditer(texto):
        verbo = m.group(1).lower()
        contexto = texto[max(0, m.start() - 200):m.end() + 60]
        peticiones.append({
            "tipo": "retiro" if verbo in _RETIRO else "incorporacion",
            "asunto": _asunto(texto[m.end():]),
            "punto_mencionado": _ordinal(contexto),
        })

    if _NEGADA_RE.search(texto):
        votacion = "parcial"          # el pleno concedió una petición y negó otra
    elif _UNANIME_RE.search(texto):
        votacion = "unanime"
    elif _MAYORIA_RE.search(texto):
        votacion = "mayoria"
    else:
        votacion = "no_determinable"

    retiros = [p for p in peticiones if p["tipo"] == "retiro"]
    altas = [p for p in peticiones if p["tipo"] == "incorporacion"]

    return {
        "modificado": True,
        "peticiones": peticiones,
        "n_retiros": len(retiros),
        "n_incorporaciones": len(altas),
        "votacion_de_la_modificacion": votacion,
        # Un retiro acorta el órden y una incorporación lo alarga. Hechos ambos,
        # la longitud no cambia y el desfase es invisible a cualquier conteo —
        # que es exactamente lo que ocultó el caso del acta 48.
        "invisible_al_conteo": bool(retiros and altas),
        # Primer punto afectado, cuando el acta lo nombra por su ordinal. Desde
        # ahí, la numeración del índice deja de coincidir con la del cuerpo.
        "desde_punto": min(
            (p["punto_mencionado"] for p in peticiones if p["punto_mencionado"]), default=None
        ),
        "reimpresiones_del_orden": reimpresiones,
        # Las dos señales deben coincidir; si no, el acta merece una mirada.
        "revisar": reimpresiones < 3,
    }


# --- CLI ---------------------------------------------------------------------


def _actas_por_id() -> dict[str, dict]:
    d = json.loads((RAIZ / "data" / "actas.json").read_text(encoding="utf-8"))
    filas = d["actas"] if isinstance(d, dict) and "actas" in d else d
    return {a["id"]: a for a in filas}


def main() -> None:
    ap = argparse.ArgumentParser(description="Estructura de sesión por acta.")
    ap.add_argument("--dry-run", action="store_true", help="no escribe, sólo el resumen")
    args = ap.parse_args()

    indice = _actas_por_id()
    fuentes = sorted(DIR_OCR.glob("*.json"), key=lambda p: int(re.sub(r"\D", "", p.stem) or 0))
    if not args.dry_run:
        DIR_SALIDA.mkdir(parents=True, exist_ok=True)

    tipos: dict[str, int] = {}
    modificadas: list[tuple[int, dict]] = []
    sin_tipo: list[int] = []
    por_firma: list[int] = []
    discrepan: list[int] = []

    for f in fuentes:
        ocr = json.loads(f.read_text(encoding="utf-8"))
        # Se lee el texto limpio, no el crudo: el membrete del acta se cuela a
        # mitad de frase en cada salto de página y llega a partir en dos las
        # frases que este módulo ancla — en el acta 54 corta "Sesión
        # Extraordinaria" por la mitad ("para celebrar Ses | ACTA DE CABILDO |
        # ión Extraordinaria"), y sin limpiar el tipo se pierde. `limpiar()` sólo
        # quita basura estructural; no reescribe palabras.
        texto = limpiar(ocr["texto_completo"])
        acta = indice.get(ocr["id"], {})

        sesion = tipo_sesion(texto, ocr["no_acta"])
        tipo = sesion["tipo"]
        tipos[tipo] = tipos.get(tipo, 0) + 1
        if tipo == "no_determinable":
            sin_tipo.append(ocr["no_acta"])
        if sesion["fuente"] == "firma":
            por_firma.append(ocr["no_acta"])
        if sesion["concuerdan"] is False:
            discrepan.append(ocr["no_acta"])

        mod = modificacion(texto)
        if mod:
            modificadas.append((ocr["no_acta"], mod))

        if not args.dry_run:
            (DIR_SALIDA / f"{ocr['id']}.json").write_text(
                json.dumps({
                    "id": ocr["id"],
                    "no_acta": ocr["no_acta"],
                    "fecha": ocr.get("fecha"),
                    "periodo": ocr.get("periodo"),
                    "tipo_sesion": sesion,
                    "n_agenda_indice": len(acta.get("agenda_items", [])),
                    "orden_del_dia_modificado": mod,
                }, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    total = len(fuentes)
    print(f"actas leídas: {total}")
    print("tipo de sesión: " + ", ".join(f"{k}={v}" for k, v in sorted(tipos.items())))
    print(f"  recuperadas del bloque de firmas (encabezado ilegible): {por_firma or 'ninguna'}")
    if sin_tipo:
        print(f"  sin tipo legible en ninguna de las dos: actas {sin_tipo}")
    if discrepan:
        print(f"  ¡encabezado y firma NO coinciden!: actas {discrepan}")

    print(f"\nórden del día modificado en sesión: {len(modificadas)}/{total}")
    con_asunto = sum(1 for _, m in modificadas if any(p["asunto"] for p in m["peticiones"]))
    con_punto = sum(1 for _, m in modificadas if m["desde_punto"])
    print(f"  con el asunto transcrito: {con_asunto}/{len(modificadas)}")
    print(f"  con el punto afectado nombrado: {con_punto}/{len(modificadas)}")
    votos: dict[str, int] = {}
    for _, m in modificadas:
        v = m["votacion_de_la_modificacion"]
        votos[v] = votos.get(v, 0) + 1
    print("  cómo se votó la modificación: " + ", ".join(f"{k}={v}" for k, v in sorted(votos.items())))
    invis = [n for n, m in modificadas if m["invisible_al_conteo"]]
    print(f"  desfase invisible al conteo (retira e incorpora): {len(invis)} → actas {invis}")
    revisar = [n for n, m in modificadas if m["revisar"]]
    print(f"  señales discrepantes, revisar: {revisar or 'ninguna'}")

    print("\nactas cuya numeración del índice ya no vale para el cuerpo del acta:")
    print("  " + ", ".join(str(n) for n, _ in modificadas))


if __name__ == "__main__":
    main()
