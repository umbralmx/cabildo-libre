#!/usr/bin/env python3
"""Phase 2, stage 2 — plain-language summaries + outcome per agenda item.

Reads the OCR text produced by `ocr_colima.py` and, for each session, asks an
LLM to (a) restate each agenda point in plain Spanish, (b) record its outcome
*only when the acta states it clearly*, and (c) extract Tier A structured fields
for Phase 3 analytics — categoría, votación, colonias, obras and explicitly
declared montos — as a byproduct of the same call. Writes one JSON per acta to
`data/summaries/<id>.json`. The structured fields obey the same honesty rule as
the outcome: only what the acta declares, never inferred (see `parse_summary`).

Provider: DeepSeek (`deepseek-v4-flash`, OpenAI-compatible). The single network
call lives in `call_llm()` — swap that one function (base URL, model, auth
header) to move to any OpenAI-compatible endpoint or to a vision model later,
without touching the rest of the pipeline. See docs/phase2-ocr-spike.md for why
DeepSeek was chosen and the quality trade-off it carries.

The input text is **OCR of a scanned document** and is noisy — mangled roman
numerals, stray characters, imperfect proper names. The prompt tells the model
to read through that noise for meaning but to **never invent an outcome**: when
the sense of the vote isn't legible, it must return `no_determinable`. That
keeps the project's rule — *never fill a gap in the source by inference* — intact
even though a summarizer is involved.

Requires DEEPSEEK_API_KEY in the environment (a GitHub Actions secret in CI).

Usage:
    python3 processor/summarize_colima.py                 # all OCR'd, pending
    python3 processor/summarize_colima.py --limit 10      # CI batch
    python3 processor/summarize_colima.py --id 2024-2027-1 --force
    python3 processor/summarize_colima.py --dry-run       # print prompt, no API call
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import urllib.request
from pathlib import Path

from limpieza import limpiar
from roster_match import build_index, emparejar

ROOT = Path(__file__).resolve().parent.parent
ACTAS_JSON = ROOT / "data" / "actas.json"
OCR_DIR = ROOT / "data" / "ocr"
SUMMARY_DIR = ROOT / "data" / "summaries"

# --- provider config (the only provider-specific surface) ---------------------
LLM_ENDPOINT = os.environ.get("LLM_ENDPOINT", "https://api.deepseek.com/chat/completions")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-v4-flash")
LLM_API_KEY_ENV = os.environ.get("LLM_API_KEY_ENV", "DEEPSEEK_API_KEY")

OCR_TEXT_CAP = 45000  # chars of acta text sent per request (keeps cost bounded)

SISTEMA = (
    "Eres un asistente que explica, en español claro y sobrio, las decisiones de "
    "un cabildo municipal mexicano, para que cualquier vecino las entienda. "
    "Recibes el órden del día de una sesión y el texto OCR del acta escaneada. "
    "El OCR es ruidoso: numerales romanos mal leídos, caracteres sueltos, nombres "
    "propios imperfectos. Interpreta el sentido a pesar del ruido, pero NO inventes "
    "datos. Nunca inventes el resultado de una votación: si el acta no dice con "
    "claridad qué se resolvió en un punto, marca su sentido como 'no_determinable'. "
    "Nunca inventes montos, colonias ni obras: sólo reporta los que el acta declare "
    "de forma explícita; ante la duda, deja la lista vacía. "
    "No uses signos de admiración, ni emoji, ni adjetivos de bombo. Frases completas."
)

INSTRUCCION = (
    "Primero redacta un 'resumen_sesion': UNA sola frase (máx. ~30 palabras), en "
    "lenguaje llano, que le diga a un vecino de qué trató esta sesión en conjunto — "
    "los asuntos de fondo que se decidieron, no el trámite. Nombra lo concreto "
    "(colonias, obras, licencias, montos) si aparece. No inventes; si la sesión sólo "
    "tuvo trámites o el texto no alcanza, dilo con sobriedad.\n\n"
    "Luego, para cada punto del órden del día, redacta una FICHA DE DECISIÓN con estos "
    "campos:\n"
    "- resumen: la decisión en una o dos frases llanas y concretas — QUÉ se resolvió, A "
    "QUIÉN beneficia y CON CUÁNTO dinero si aplica. Nada de relleno genérico.\n"
    "- sentido: uno de exactamente estos valores, según lo que el acta declare: "
    "'aprobado', 'rechazado', 'aplazado', 'retirado', 'tramite' (puntos de mero "
    "procedimiento: lista de asistencia, quórum, lectura del órden, clausura), o "
    "'no_determinable' si el texto no permite afirmar el resultado.\n"
    "- categoria: el tipo de asunto, UNO de exactamente: 'obra_publica', 'licencia', "
    "'fraccionamiento', 'presupuesto_finanzas', 'nombramiento', 'convenio', "
    "'reglamento_normativo', 'patrimonio', 'tramite' (procedimiento interno), u 'otro'. "
    "Elige la que mejor describa el fondo del punto.\n"
    "- votacion: cómo se votó, UNO de: 'unanime', 'mayoria', o 'no_determinable' si el "
    "acta no lo dice. Es distinto del sentido: describe la forma de la votación, no su "
    "resultado.\n"
    "- colonias: lista de nombres de colonias, fraccionamientos o localidades que el acta "
    "mencione EN ESTE PUNTO, tal como aparecen. Lista vacía si no menciona ninguna.\n"
    "- obras: lista de obras, calles o proyectos nombrados EN ESTE PUNTO. Vacía si no hay.\n"
    "- montos: lista de cantidades de dinero que el acta declare EXPLÍCITAMENTE en este "
    "punto. Cada una es {\"texto\": <la cifra tal como aparece>, \"valor_mxn\": <el número "
    "en pesos, o null si no puedes normalizarlo con certeza>}. NUNCA inventes, estimes ni "
    "sumes cifras; NO incluyas montos de otros puntos; si el punto no declara dinero, "
    "devuelve lista vacía.\n"
    "- beneficiario: a quién se dirige el recurso o el acto (la contraparte de un convenio, "
    "la empresa de una obra, la persona nombrada, la dependencia). Objeto "
    "{\"nombre\": <tal como aparece>, \"tipo\": <UNO de 'empresa','persona','dependencia',"
    "'fraccionamiento','ciudadania','otro'>}, o null si el punto no lo declara.\n"
    "- votos_en_contra: lista de NOMBRES de regidores que el acta diga que votaron en contra "
    "(p. ej. 'votos en contra de las Regidoras…'), tal como los nombra. Vacía si fue unánime "
    "o si el acta no lo dice. No infieras quién.\n"
    "- abstenciones: lista de NOMBRES de regidores que se abstuvieron, según el acta. Vacía "
    "si no las hay o no se declaran.\n"
    "- comision: la comisión que dictamina o presenta el punto (p. ej. 'Comisión de "
    "Hacienda'), tal como aparece, o null.\n"
    "- autor: NOMBRE del regidor que presenta o da lectura al dictamen, o null si no se dice.\n"
    "Responde SOLO con JSON válido, sin texto alrededor, con esta forma:\n"
    '{"resumen_sesion": "...", "puntos": [{"n": <entero>, "resumen": "...", '
    '"sentido": "...", "categoria": "...", "votacion": "...", "colonias": [], '
    '"obras": [], "montos": [{"texto": "...", "valor_mxn": null}], '
    '"beneficiario": {"nombre": "...", "tipo": "..."}, "votos_en_contra": [], '
    '"abstenciones": [], "comision": null, "autor": null}]}'
)

SENTIDOS = {"aprobado", "rechazado", "aplazado", "retirado", "tramite", "no_determinable"}
CATEGORIAS = {
    "obra_publica", "licencia", "fraccionamiento", "presupuesto_finanzas",
    "nombramiento", "convenio", "reglamento_normativo", "patrimonio", "tramite", "otro",
}
VOTACIONES = {"unanime", "mayoria", "no_determinable"}
BENEFICIARIO_TIPOS = {"empresa", "persona", "dependencia", "fraccionamiento", "ciudadania", "otro"}
ESQUEMA = 3  # bumped when the per-punto shape changes; lets the aggregator tell tiers apart

_ROSTER = build_index()  # for mapping dissenter/abstainer/author names to roster ids


def build_messages(acta: dict, ocr_text: str) -> list[dict]:
    agenda = "\n".join(
        f"{it['n']}. ({it.get('numeral') or '·'}) {it['texto']}"
        for it in acta["agenda_items"]
    )
    user = (
        f"{INSTRUCCION}\n\n"
        f"=== ÓRDEN DEL DÍA (acta {acta['no_acta']}, {acta['fecha']}) ===\n{agenda}\n\n"
        f"=== TEXTO OCR DEL ACTA (puede estar truncado) ===\n{ocr_text[:OCR_TEXT_CAP]}"
    )
    return [{"role": "system", "content": SISTEMA}, {"role": "user", "content": user}]


def call_llm(messages: list[dict]) -> str:
    """The one provider-specific call. Returns the model's raw text response."""
    api_key = os.environ.get(LLM_API_KEY_ENV)
    if not api_key:
        sys.exit(f"ERROR: {LLM_API_KEY_ENV} not set — needed to call the summary model.")
    body = json.dumps({
        "model": LLM_MODEL,
        "messages": messages,
        "stream": False,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    req = urllib.request.Request(
        LLM_ENDPOINT, data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def _clean_strings(raw: object, cap: int = 12, maxlen: int = 80) -> list[str]:
    """Coerce a model field into a deduped list of trimmed strings, capped."""
    if not isinstance(raw, list):
        return []
    seen: set[str] = set()
    out: list[str] = []
    for s in raw:
        if not isinstance(s, str):
            continue
        s = s.strip()[:maxlen]
        key = s.lower()
        if s and key not in seen:
            seen.add(key)
            out.append(s)
    return out[:cap]


def _clean_montos(raw: object, cap: int = 20) -> list[dict]:
    """Keep only amounts with a literal text; carry a numeric value only when the
    model gave a real number (never coerce a string into one — that would fabricate
    precision the acta didn't state)."""
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for m in raw:
        if isinstance(m, dict):
            texto = (m.get("texto") or "").strip()
            val = m.get("valor_mxn")
        elif isinstance(m, str):
            texto, val = m.strip(), None
        else:
            continue
        if not texto:
            continue
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            val = None
        out.append({"texto": texto[:120], "valor_mxn": val})
        if len(out) >= cap:
            break
    return out


def _clean_beneficiario(raw: object) -> dict | None:
    """A {nombre, tipo} object, or None. Never invented: only kept when the model
    gave a name."""
    if not isinstance(raw, dict):
        return None
    nombre = (raw.get("nombre") or "").strip()
    if not nombre:
        return None
    tipo = raw.get("tipo")
    return {"nombre": nombre[:120], "tipo": tipo if tipo in BENEFICIARIO_TIPOS else "otro"}


def _clean_personas(raw: object, cap: int = 13) -> list[dict]:
    """Model-named regidores → [{nombre, id}] mapped to the roster. An unmatched
    name keeps id None (a suplente or an OCR-garbled name), never forced onto a
    roster slot — same honesty rule as the attendance extractor."""
    out: list[dict] = []
    seen: set[str] = set()
    for s in _clean_strings(raw, cap=cap, maxlen=80):
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({"nombre": s, "id": emparejar(s, _ROSTER)})
    return out


def parse_summary(raw: str, acta: dict) -> tuple[str, list[dict]]:
    """Validate the model output against the agenda; drop anything malformed.
    Returns (resumen_sesion, puntos)."""
    try:
        payload = json.loads(raw)
        rows = payload["puntos"]
    except (json.JSONDecodeError, KeyError, TypeError):
        raise ValueError("model did not return the expected JSON shape")

    resumen_sesion = (payload.get("resumen_sesion") or "").strip()
    by_n = {it["n"]: it for it in acta["agenda_items"]}
    out = []
    for row in rows:
        n = row.get("n")
        if n not in by_n:
            continue  # hallucinated point number — discard
        sentido = row.get("sentido")
        categoria = row.get("categoria")
        votacion = row.get("votacion")
        comision = (row.get("comision") or "").strip() if isinstance(row.get("comision"), str) else None
        autor_nombre = (row.get("autor") or "").strip() if isinstance(row.get("autor"), str) else ""
        out.append({
            "n": n,
            "numeral": by_n[n].get("numeral"),
            "resumen": (row.get("resumen") or "").strip(),
            "sentido": sentido if sentido in SENTIDOS else "no_determinable",
            "categoria": categoria if categoria in CATEGORIAS else "otro",
            "votacion": votacion if votacion in VOTACIONES else "no_determinable",
            "colonias": _clean_strings(row.get("colonias")),
            "obras": _clean_strings(row.get("obras")),
            "montos": _clean_montos(row.get("montos")),
            "beneficiario": _clean_beneficiario(row.get("beneficiario")),
            "votos_en_contra": _clean_personas(row.get("votos_en_contra")),
            "abstenciones": _clean_personas(row.get("abstenciones")),
            "comision": comision or None,
            "autor": ({"nombre": autor_nombre[:120], "id": emparejar(autor_nombre, _ROSTER)}
                      if autor_nombre else None),
        })
    return resumen_sesion, out


def summarize_acta(acta: dict, ocr: dict, dry_run: bool) -> dict | None:
    # Feed the model the cleaned text: less structural noise fits more real
    # content under OCR_TEXT_CAP and sharpens extraction. Raw stays as evidence.
    messages = build_messages(acta, limpiar(ocr["texto_completo"]))
    if dry_run:
        print(messages[1]["content"][:1500])
        return None
    raw = call_llm(messages)
    resumen_sesion, puntos = parse_summary(raw, acta)
    return {
        "id": acta["id"],
        "no_acta": acta["no_acta"],
        "fecha": acta["fecha"],
        "periodo": acta["periodo"],
        "esquema": ESQUEMA,
        "modelo": LLM_MODEL,
        "fuente_texto": ocr["motor"],
        "generado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "resumen_sesion": resumen_sesion,
        "puntos": puntos,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--id", help="summarize a single acta by id")
    ap.add_argument("--limit", type=int, help="process at most N pending actas")
    ap.add_argument("--force", action="store_true", help="re-summarize even if cached")
    ap.add_argument("--dry-run", action="store_true", help="print the prompt, no API call")
    args = ap.parse_args()

    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    actas = {a["id"]: a for a in json.loads(ACTAS_JSON.read_text(encoding="utf-8"))["actas"]}

    ocr_ids = [args.id] if args.id else sorted(p.stem for p in OCR_DIR.glob("*.json"))
    pending = [i for i in ocr_ids
               if i in actas and (args.force or not (SUMMARY_DIR / f"{i}.json").exists())]
    if args.limit:
        pending = pending[:args.limit]

    print(f"OCR'd actas: {len(ocr_ids)} | summaries pending: {len(pending)} | model: {LLM_MODEL}")

    ok = 0
    for acta_id in pending:
        ocr = json.loads((OCR_DIR / f"{acta_id}.json").read_text(encoding="utf-8"))
        print(f"[{acta_id}] {actas[acta_id]['fecha']} …")
        try:
            result = summarize_acta(actas[acta_id], ocr, args.dry_run)
        except (ValueError, KeyError, OSError) as e:
            print(f"  ! {e}; skipping")
            continue
        if result is None:  # dry run
            continue
        (SUMMARY_DIR / f"{acta_id}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        n_det = sum(1 for p in result["puntos"] if p["sentido"] not in ("no_determinable", "tramite"))
        print(f"  → {len(result['puntos'])} puntos ({n_det} con sentido determinado)")
        ok += 1

    print(f"done: {ok} summarized this run")


if __name__ == "__main__":
    main()
