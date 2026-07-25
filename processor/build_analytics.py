#!/usr/bin/env python3
"""Phase 3 (L3) — aggregate the per-acta data into one static analytics payload.

Rolls up what the Tier A summaries and the attendance extractor produced into
`site/analytics-<termino>.json`, ready for the dashboards (L4). No API, no
database — reads `data/summaries/` + `data/asistencia/` and writes one JSON.

**Honesty is structural here, because aggregates hide their own gaps:**

  * *Coverage is reported, not assumed.* The term has 74 actas; only some are
    OCR'd/summarized, and the Tier A fields (categoría, votación, colonias,
    montos) exist only on `esquema >= 2` summaries. Every section states the
    base it was computed over (`cobertura`), so a chart can't imply the whole
    term when it saw a handful of sessions.
  * *Montos are "declared", never "total".* `suma_declarada_mxn` is the sum of
    the amounts the actas state explicitly — not the municipal budget. The nota
    field carries that caveat into the payload so L4 can't drop it.
  * *Attendance rates exclude the illegible.* `no_determinable` sessions are out
    of the denominator, so a bad scan neither counts as present nor as absent.
  * *Suplentes are listed as found*, under `suplencias`, not merged into anyone.
  * *The decision-record sections (`esquema >= 3`) count only their own base.*
    Dissent, abstentions, authorship, comisiones and beneficiarios exist only on
    L5 summaries, so each of those sections carries its own `cobertura` — an
    older summary that never had the field is absent, not a zero. A regidor with
    no recorded dissent means "no acta we read named them", never "they always
    agreed"; the payload says so in `nota`.

Usage:
    python3 processor/build_analytics.py                 # term 2024-2027
    python3 processor/build_analytics.py --termino 2024-2027
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACTAS_JSON = ROOT / "data" / "actas.json"
SUMMARY_DIR = ROOT / "data" / "summaries"
ASIST_DIR = ROOT / "data" / "asistencia"
ROSTER_JSON = ROOT / "data" / "regidores-2024-2027.json"
SITE_DIR = ROOT / "site"

SENTIDOS_DECISION = ("aprobado", "rechazado", "aplazado", "retirado", "no_determinable")
ESTADOS = ("presente", "remoto", "falta_justificada", "ausente", "no_determinable")


def _norm(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def _clean_colonia(name: str) -> str:
    """Drop the leading 'Colonia/Fracc./Barrio' label so 'Colonia Fátima' and
    'Fátima' aggregate together."""
    n = re.sub(r"^(colonia|col\.?|fracc\.?|fraccionamiento|barrio)\s+", "", name.strip(), flags=re.I)
    return n.strip(" .,")


def _suma_punto(vals: list[float]) -> tuple[float, bool]:
    """Sum one punto's declared amounts, guarding against the *total + desglose*
    pattern: an acta that approves a works package often states the grand total
    **and then lists each obra**, so adding all of them counts the same pesos
    twice (acta 53 p6: a $661.8M total plus 19 obras → a bogus $1.04B).

    When a single amount is at least as large as every other amount in the punto
    combined, and the punto lists five or more, that largest figure is read as the
    total and the rest as its breakdown — so only the total is summed. Both the
    raw and the guarded sums are published, each with its definition; neither is
    presented as *the* figure. Returns (sum, flagged)."""
    if not vals:
        return 0.0, False
    mayor = max(vals)
    resto = sum(vals) - mayor
    if len(vals) >= 5 and mayor >= 0.98 * resto:
        return mayor, True
    return sum(vals), False


def _personas(raw: object) -> list[dict]:
    """The `[{nombre, id}]` shape the L5 summarizer emits, defensively read. An
    entry whose `id` is None was named by the acta but matched no roster member
    (a suplente, or a name the OCR mangled) — it is kept as a name, never
    reassigned to whoever looks closest."""
    if not isinstance(raw, list):
        return []
    out = []
    for r in raw:
        if isinstance(r, dict) and (r.get("nombre") or "").strip():
            out.append({"nombre": r["nombre"].strip(), "id": r.get("id") or None})
    return out


def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def build(termino: str) -> dict:
    actas = {a["id"]: a for a in load_json(ACTAS_JSON)["actas"]}
    term_ids = {i for i, a in actas.items() if a.get("periodo") == termino}
    roster = load_json(ROSTER_JSON)["integrantes"]
    nombre_de = {m["id"]: m for m in roster}

    summaries = sorted(p for p in SUMMARY_DIR.glob("*.json") if p.stem in term_ids)
    asistencias = sorted(p for p in ASIST_DIR.glob("*.json") if p.stem in term_ids)

    # --- reading depth (N1) ---------------------------------------------------
    # The dashboard already says how many actas it read; this says how much of
    # each one. Summaries written before the windowing fix carry no `lectura`, and
    # that is reported as unknown rather than guessed from the old cap.
    chars_ocr = chars_leidos = 0
    actas_completas = lectura_sin_dato = ventanas_fallidas = 0
    conflictos_puntos: list[dict] = []

    # --- session calendar (I3) + integrity (T3) -------------------------------
    # Built from actas.json, so it covers all 74 sessions of the term, not only
    # the processed ones — the one part of the panel with full coverage.
    procesadas = {p.stem for p in SUMMARY_DIR.glob("*.json")}
    calendario, sin_agenda, sin_pdf, sin_fecha = [], [], [], []
    for i in sorted(term_ids, key=lambda x: (actas[x].get("fecha") or "", x)):
        a = actas[i]
        n_items = len(a.get("agenda_items") or [])
        calendario.append({
            "acta": i, "no_acta": a.get("no_acta"), "fecha": a.get("fecha"),
            "n_puntos": n_items, "procesada": i in procesadas, "pdf_url": a.get("pdf_url"),
        })
        if not n_items:
            sin_agenda.append(a.get("no_acta"))
        if not a.get("pdf_url"):
            sin_pdf.append(a.get("no_acta"))
        if not a.get("fecha"):
            sin_fecha.append(a.get("no_acta"))
    numeros = sorted(int(a["no_acta"]) for a in (actas[i] for i in term_ids) if a.get("no_acta"))
    huecos = [n for n in range(numeros[0], numeros[-1] + 1) if n not in set(numeros)] if numeros else []
    # The source numbers two different sessions the same, and skips one. Reported,
    # never renumbered: the inconsistency is the ayuntamiento's record, not ours.
    duplicados = sorted(n for n, k in Counter(numeros).items() if k > 1)

    # --- decisions (sentido for all; Tier A on esquema >= 2; ficha on >= 3) ----
    por_sentido: Counter[str] = Counter()
    por_categoria: Counter[str] = Counter()
    por_votacion: Counter[str] = Counter()
    colonia_surface: dict[str, Counter[str]] = defaultdict(Counter)  # key -> {surface: n}
    montos: list[dict] = []
    suma_guardada = 0.0          # per-punto sums with the total+desglose guard
    total_desglose: list[dict] = []
    n_puntos = n_sustantivos = 0
    n_tier_a = n_ficha = 0

    # L5 (esquema 3) roll-ups. Kept on their own counters with their own base:
    # a pre-L5 summary simply never had these fields, which is not a zero.
    n_puntos_ficha = 0
    contra_por_id: Counter[str] = Counter()
    abst_por_id: Counter[str] = Counter()
    autoria_por_id: Counter[str] = Counter()
    sin_mapear: Counter[str] = Counter()          # named but not on the roster
    comisiones: Counter[str] = Counter()
    benef_surface: dict[str, Counter[str]] = defaultdict(Counter)
    benef_datos: dict[str, dict] = {}
    disenso_cat: dict[str, Counter[str]] = defaultdict(Counter)
    disidencias: list[dict] = []

    for p in summaries:
        d = load_json(p)
        esquema = d.get("esquema", 1)
        tier_a = esquema >= 2
        ficha = esquema >= 3
        n_tier_a += tier_a
        n_ficha += ficha

        lec = d.get("lectura")
        if isinstance(lec, dict) and lec.get("chars_ocr"):
            chars_ocr += lec["chars_ocr"]
            chars_leidos += min(lec.get("chars_leidos", 0), lec["chars_ocr"])
            actas_completas += bool(lec.get("completa"))
            ventanas_fallidas += lec.get("ventanas_fallidas", 0)
        else:
            lectura_sin_dato += 1
        for n in d.get("puntos_en_conflicto") or []:
            conflictos_puntos.append({"acta": d["id"], "no_acta": d.get("no_acta"), "punto": n})
        for pt in d["puntos"]:
            n_puntos += 1
            sent = pt.get("sentido", "no_determinable")
            if sent == "tramite":
                continue  # procedural: not a decision
            n_sustantivos += 1
            por_sentido[sent] += 1
            if not tier_a:
                continue
            categoria = pt.get("categoria", "otro")
            votacion = pt.get("votacion", "no_determinable")
            por_categoria[categoria] += 1
            por_votacion[votacion] += 1
            for col in pt.get("colonias", []):
                clean = _clean_colonia(col)
                if clean:
                    colonia_surface[_norm(clean)][clean] += 1
            punto_montos = []
            for m in pt.get("montos", []):
                val = m.get("valor_mxn")
                val = val if isinstance(val, (int, float)) and not isinstance(val, bool) else None
                punto_montos.append(val)
                montos.append({
                    "texto": m.get("texto", ""),
                    "valor_mxn": val,
                    "acta": d["id"], "no_acta": d.get("no_acta"), "punto": pt["n"],
                })
            con_valor_pt = [v for v in punto_montos if v is not None]
            suma_pt, es_total_desglose = _suma_punto(con_valor_pt)
            suma_guardada += suma_pt
            if es_total_desglose:
                total_desglose.append({
                    "acta": d["id"], "no_acta": d.get("no_acta"), "punto": pt["n"],
                    "total_mxn": max(con_valor_pt), "n_componentes": len(con_valor_pt) - 1,
                    "suma_componentes_mxn": round(sum(con_valor_pt) - max(con_valor_pt), 2),
                })

            if not ficha:
                continue

            # --- decision record: to whom, who dissented, who presented it -----
            n_puntos_ficha += 1
            contra = _personas(pt.get("votos_en_contra"))
            abst = _personas(pt.get("abstenciones"))
            for who in contra:
                (contra_por_id if who["id"] else sin_mapear)[who["id"] or who["nombre"]] += 1
            for who in abst:
                (abst_por_id if who["id"] else sin_mapear)[who["id"] or who["nombre"]] += 1

            # D5 — dissent by categoría. `puntos` is the base so a rate is honest.
            dc = disenso_cat[categoria]
            dc["puntos"] += 1
            dc["mayoria"] += votacion == "mayoria"
            if contra:
                dc["con_votos_en_contra"] += 1
                dc["votos_en_contra"] += len(contra)
            if abst:
                dc["con_abstenciones"] += 1

            if contra or abst:
                disidencias.append({
                    "acta": d["id"], "no_acta": d.get("no_acta"), "fecha": d.get("fecha"),
                    "punto": pt["n"], "categoria": categoria, "votacion": votacion,
                    "resumen": pt.get("resumen", ""),
                    "votos_en_contra": contra, "abstenciones": abst,
                })

            com = (pt.get("comision") or "").strip()
            if com:
                comisiones[com] += 1
            autor = pt.get("autor")
            if isinstance(autor, dict):
                aid = autor.get("id")
                (autoria_por_id if aid else sin_mapear)[aid or (autor.get("nombre") or "?")] += 1

            # M5 — external counterparties, with the amounts declared alongside.
            ben = pt.get("beneficiario")
            if isinstance(ben, dict) and (ben.get("nombre") or "").strip():
                nombre = ben["nombre"].strip()
                key = _norm(nombre)
                benef_surface[key][nombre] += 1
                slot = benef_datos.setdefault(key, {"tipo": Counter(), "monto": 0.0,
                                                    "n_con_monto": 0, "actas": set()})
                slot["tipo"][ben.get("tipo") or "otro"] += 1
                slot["actas"].add(d["id"])
                if con_valor_pt:
                    slot["monto"] += suma_pt  # guarded: never total + its desglose
                    slot["n_con_monto"] += 1

    colonias = sorted(
        ({"nombre": surf.most_common(1)[0][0], "menciones": sum(surf.values())}
         for surf in colonia_surface.values()),
        key=lambda c: (-c["menciones"], c["nombre"]),
    )
    con_valor = [m for m in montos if m["valor_mxn"] is not None]
    mayores = sorted(con_valor, key=lambda m: -m["valor_mxn"])[:15]

    # --- attendance ------------------------------------------------------------
    tally: dict[str, Counter[str]] = {m["id"]: Counter() for m in roster}
    suplencias: list[dict] = []
    sesiones: list[dict] = []
    for p in asistencias:
        d = load_json(p)
        acta = actas.get(d["id"], {})
        for mid, estado in d["estados"].items():
            if mid in tally:
                tally[mid][estado] += 1
        for nombre in d.get("no_reconocidos", []):
            suplencias.append({"acta": d["id"], "no_acta": acta.get("no_acta"),
                               "fecha": acta.get("fecha"), "nombre": nombre})
        r = d["resumen"]
        sesiones.append({"acta": d["id"], "no_acta": acta.get("no_acta"), "fecha": acta.get("fecha"),
                         "asistio": r.get("asistio", 0),
                         **{e: r.get(e, 0) for e in ESTADOS}})
    sesiones.sort(key=lambda s: (s["fecha"] or ""))

    por_integrante = []
    for m in roster:
        c = tally[m["id"]]
        determinables = sum(c[e] for e in ("presente", "remoto", "falta_justificada", "ausente"))
        asistio = c["presente"] + c["remoto"]
        por_integrante.append({
            "id": m["id"], "nombre": m["nombre"], "cargo": m["cargo"],
            "sesiones": sum(c.values()),
            **{e: c[e] for e in ESTADOS},
            "asistio": asistio,
            "tasa_asistencia": round(asistio / determinables, 3) if determinables else None,
        })

    # --- L5 roll-ups, shaped for the dashboard --------------------------------
    # P2/P3/P4 in one per-regidor row: dissent, abstentions, dictámenes presented.
    registro_voto = sorted(
        ({"id": m["id"], "nombre": m["nombre"], "cargo": m["cargo"],
          "votos_en_contra": contra_por_id[m["id"]],
          "abstenciones": abst_por_id[m["id"]],
          "dictamenes_presentados": autoria_por_id[m["id"]]}
         for m in roster),
        key=lambda r: (-r["votos_en_contra"], -r["abstenciones"], r["nombre"]),
    )

    beneficiarios = sorted(
        ({"nombre": benef_surface[k].most_common(1)[0][0],
          "tipo": v["tipo"].most_common(1)[0][0],
          "menciones": sum(benef_surface[k].values()),
          "actas": len(v["actas"]),
          "monto_declarado_mxn": round(v["monto"], 2) if v["n_con_monto"] else None,
          "puntos_con_monto": v["n_con_monto"]}
         for k, v in benef_datos.items()),
        key=lambda b: (-b["menciones"], -(b["monto_declarado_mxn"] or 0), b["nombre"]),
    )

    disenso_por_categoria = sorted(
        ({"categoria": cat, "puntos": c["puntos"], "mayoria": c["mayoria"],
          "con_votos_en_contra": c["con_votos_en_contra"],
          "votos_en_contra": c["votos_en_contra"],
          "con_abstenciones": c["con_abstenciones"],
          "tasa_disenso": round(c["con_votos_en_contra"] / c["puntos"], 3) if c["puntos"] else None}
         for cat, c in disenso_cat.items()),
        key=lambda r: (-r["tasa_disenso"] if r["tasa_disenso"] is not None else 0, -r["puntos"]),
    )
    disidencias.sort(key=lambda x: (x["fecha"] or "", x["punto"]))

    return {
        "termino": termino,
        "municipio": "Colima",
        "generado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "cobertura": {
            "actas_en_termino": len(term_ids),
            "con_resumen": len(summaries),
            "con_tier_a": n_tier_a,
            "con_ficha_decision": n_ficha,
            "con_asistencia": len(asistencias),
            "nota": (f"Análisis parcial: {len(summaries)} de {len(term_ids)} actas del término "
                     f"tienen resumen, {n_tier_a} tienen los campos analíticos (categoría, "
                     f"votación, colonias, montos) y {n_ficha} tienen ficha de decisión "
                     "(beneficiario, votos en contra, abstenciones, comisión, autoría). "
                     "Las cifras crecen conforme avanza el procesamiento."),
        },
        "decisiones": {
            "n_puntos": n_puntos,
            "n_sustantivos": n_sustantivos,
            "por_sentido": dict(por_sentido.most_common()),
            "por_categoria": dict(por_categoria.most_common()),
            "por_votacion": dict(por_votacion.most_common()),
            "base_tier_a": "categoría y votación se cuentan sólo sobre los puntos con campos analíticos.",
        },
        "montos": {
            "n_declarados": len(montos),
            "n_con_valor": len(con_valor),
            "suma_bruta_mxn": round(sum(m["valor_mxn"] for m in con_valor), 2),
            "suma_declarada_mxn": round(suma_guardada, 2),
            "puntos_total_y_desglose": total_desglose,
            "nota": ("Suma de los montos que las actas declaran de forma explícita; NO es el "
                     "presupuesto del municipio ni el gasto total, sólo lo nombrado en los puntos "
                     "analizados. Un punto suele declarar el total de un paquete de obra Y el "
                     "desglose obra por obra: sumar ambos contaría los mismos pesos dos veces, así "
                     "que cuando un monto iguala o supera a todos los demás del punto juntos (y el "
                     "punto lista cinco o más) se toma sólo ese total. `suma_declarada_mxn` aplica "
                     "esa regla y es la cifra a mostrar; `suma_bruta_mxn` es la suma sin corregir, "
                     "publicada para que la diferencia sea auditable; los puntos afectados se listan "
                     "en `puntos_total_y_desglose`."),
            "mayores": mayores,
        },
        # N1 — how much of the expediente was actually read. The caveat the rest
        # of the panel leans on: coverage in actas is not coverage in text.
        "lectura": {
            "chars_ocr": chars_ocr,
            "chars_leidos": chars_leidos,
            "proporcion": round(chars_leidos / chars_ocr, 4) if chars_ocr else None,
            "actas_completas": actas_completas,
            "actas_con_dato": len(summaries) - lectura_sin_dato,
            "actas_sin_dato": lectura_sin_dato,
            "ventanas_fallidas": ventanas_fallidas,
            "puntos_en_conflicto": conflictos_puntos,
            "nota": ("Proporción del texto OCR de cada acta que llegó al modelo que redacta "
                     "los resúmenes. Un acta se lee en ventanas solapadas; si una ventana "
                     "falla, su parte se descuenta aquí en vez de darse por leída. "
                     "`puntos_en_conflicto` son los puntos en que dos ventanas afirmaron "
                     "resultados distintos: se resolvió por mayoría y se listan para poder "
                     "verificarlos contra el PDF. Las actas resumidas antes de esta medición "
                     "aparecen en `actas_sin_dato`: no se les supone cobertura."),
        },
        # I3 + T3 — the only full-coverage part of the panel: it comes from the
        # index (Fase 1), not from the OCR, so it describes all 74 sessions.
        "calendario": {
            "sesiones": calendario,
            "nota": ("Las 74 sesiones del término según el índice oficial, procesadas o no. "
                     "Esta sección no depende del OCR."),
        },
        "integridad": {
            "actas_en_termino": len(term_ids),
            "sin_agenda_publicada": sin_agenda,
            "sin_enlace_pdf": sin_pdf,
            "sin_fecha_publicada": sin_fecha,
            "huecos_de_numeracion": huecos,
            "numeros_duplicados": duplicados,
            "nota": ("Vacíos de la fuente, no imputados: sesiones cuyo órden del día no "
                     "aparece en el índice, sin enlace al PDF o sin fecha, números de acta "
                     "ausentes en el rango del término, y números que la fuente asigna a dos "
                     "sesiones distintas. Se declaran tal como están: no se renumera ni se "
                     "rellena nada."),
        },
        "colonias": colonias,
        # --- L5 sections. Each states the base it saw, so a thin backfill reads
        # as thin coverage rather than as a council that never disagreed. -------
        "registro_voto": {
            "base_actas": n_ficha,
            "base_puntos": n_puntos_ficha,
            "por_integrante": registro_voto,
            "eventos": disidencias,
            "nombres_sin_mapear": [{"nombre": n, "menciones": c}
                                   for n, c in sin_mapear.most_common()],
            "nota": ("Sólo cuenta lo que el acta nombra explícitamente: un cero no significa "
                     "que la persona siempre votó a favor, sino que ninguna de las "
                     f"{n_ficha} actas con ficha de decisión la nombró votando en contra o "
                     "absteniéndose. Los nombres que no corresponden a ningún integrante del "
                     "cabildo (suplentes, o nombres que el OCR deformó) se listan aparte en "
                     "nombres_sin_mapear, sin asignarlos a nadie."),
        },
        "disenso_por_categoria": {
            "base_puntos": n_puntos_ficha,
            "filas": disenso_por_categoria,
            "nota": ("tasa_disenso = puntos con votos en contra nombrados / puntos de esa "
                     "categoría con ficha de decisión. Un dictamen aprobado por mayoría cuya "
                     "acta no nombra a los disidentes cuenta en 'mayoria' pero no en "
                     "'con_votos_en_contra'."),
        },
        "beneficiarios": {
            "base_puntos": n_puntos_ficha,
            "filas": beneficiarios,
            "nota": ("Contrapartes tal como el acta las nombra. monto_declarado_mxn suma los "
                     "montos declarados en los puntos donde aparece la contraparte —con la "
                     "misma regla anti-doble-conteo que la sección de montos—: es lo que el "
                     "acta dice, no un contrato verificado ni un pago ejercido. La recurrencia "
                     "se registra; no implica irregularidad."),
        },
        "comisiones": {
            "base_puntos": n_puntos_ficha,
            "filas": [{"nombre": c, "puntos": n} for c, n in comisiones.most_common()],
            "nota": ("Comisión que dictamina el punto, tal como aparece. Un punto puede "
                     "involucrar a más de una comisión; se registra la que dictamina, y los "
                     "nombres no están normalizados entre actas."),
        },
        "asistencia": {
            "sesiones_consideradas": len(asistencias),
            "por_integrante": por_integrante,
            "suplencias": suplencias,
            "sesiones": sesiones,
            "nota": ("La tasa de asistencia excluye las sesiones en que el OCR no permite leer el "
                     "pase de lista (no_determinable), para no contarlas ni como presencia ni como falta."),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--termino", default="2024-2027")
    args = ap.parse_args()

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    payload = build(args.termino)
    out = SITE_DIR / f"analytics-{args.termino}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    cob = payload["cobertura"]
    print(f"analytics {args.termino}: {cob['con_resumen']}/{cob['actas_en_termino']} con resumen, "
          f"{cob['con_tier_a']} con Tier A, {cob['con_ficha_decision']} con ficha, "
          f"{cob['con_asistencia']} con asistencia")
    print(f"  decisiones sustantivas: {payload['decisiones']['n_sustantivos']} | "
          f"montos con valor: {payload['montos']['n_con_valor']} "
          f"(suma ${payload['montos']['suma_declarada_mxn']:,.2f}) | "
          f"colonias: {len(payload['colonias'])} | suplencias: {len(payload['asistencia']['suplencias'])}")
    rv = payload["registro_voto"]
    print(f"  ficha: {rv['base_puntos']} puntos | "
          f"eventos de disenso/abstención: {len(rv['eventos'])} | "
          f"contrapartes: {len(payload['beneficiarios']['filas'])} | "
          f"comisiones: {len(payload['comisiones']['filas'])} | "
          f"nombres sin mapear: {len(rv['nombres_sin_mapear'])}")
    print(f"  → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
