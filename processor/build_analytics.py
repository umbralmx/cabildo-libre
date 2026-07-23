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


def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def build(termino: str) -> dict:
    actas = {a["id"]: a for a in load_json(ACTAS_JSON)["actas"]}
    term_ids = {i for i, a in actas.items() if a.get("periodo") == termino}
    roster = load_json(ROSTER_JSON)["integrantes"]
    nombre_de = {m["id"]: m for m in roster}

    summaries = sorted(p for p in SUMMARY_DIR.glob("*.json") if p.stem in term_ids)
    asistencias = sorted(p for p in ASIST_DIR.glob("*.json") if p.stem in term_ids)

    # --- decisions (sentido for all; Tier A only where esquema >= 2) -----------
    por_sentido: Counter[str] = Counter()
    por_categoria: Counter[str] = Counter()
    por_votacion: Counter[str] = Counter()
    colonia_surface: dict[str, Counter[str]] = defaultdict(Counter)  # key -> {surface: n}
    montos: list[dict] = []
    n_puntos = n_sustantivos = 0
    n_tier_a = 0

    for p in summaries:
        d = load_json(p)
        tier_a = d.get("esquema", 1) >= 2
        n_tier_a += tier_a
        for pt in d["puntos"]:
            n_puntos += 1
            sent = pt.get("sentido", "no_determinable")
            if sent == "tramite":
                continue  # procedural: not a decision
            n_sustantivos += 1
            por_sentido[sent] += 1
            if not tier_a:
                continue
            por_categoria[pt.get("categoria", "otro")] += 1
            por_votacion[pt.get("votacion", "no_determinable")] += 1
            for col in pt.get("colonias", []):
                clean = _clean_colonia(col)
                if clean:
                    colonia_surface[_norm(clean)][clean] += 1
            for m in pt.get("montos", []):
                val = m.get("valor_mxn")
                montos.append({
                    "texto": m.get("texto", ""),
                    "valor_mxn": val if isinstance(val, (int, float)) and not isinstance(val, bool) else None,
                    "acta": d["id"], "no_acta": d.get("no_acta"), "punto": pt["n"],
                })

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

    return {
        "termino": termino,
        "municipio": "Colima",
        "generado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "cobertura": {
            "actas_en_termino": len(term_ids),
            "con_resumen": len(summaries),
            "con_tier_a": n_tier_a,
            "con_asistencia": len(asistencias),
            "nota": (f"Análisis parcial: {len(summaries)} de {len(term_ids)} actas del término "
                     f"tienen resumen y {n_tier_a} tienen los campos analíticos (categoría, "
                     "votación, colonias, montos). Las cifras crecen conforme avanza el procesamiento."),
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
            "suma_declarada_mxn": round(sum(m["valor_mxn"] for m in con_valor), 2),
            "nota": ("Suma de los montos que las actas declaran de forma explícita; NO es el "
                     "presupuesto del municipio ni el gasto total, sólo lo nombrado en los puntos analizados."),
            "mayores": mayores,
        },
        "colonias": colonias,
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
          f"{cob['con_tier_a']} con Tier A, {cob['con_asistencia']} con asistencia")
    print(f"  decisiones sustantivas: {payload['decisiones']['n_sustantivos']} | "
          f"montos con valor: {payload['montos']['n_con_valor']} "
          f"(suma ${payload['montos']['suma_declarada_mxn']:,.2f}) | "
          f"colonias: {len(payload['colonias'])} | suplencias: {len(payload['asistencia']['suplencias'])}")
    print(f"  → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
