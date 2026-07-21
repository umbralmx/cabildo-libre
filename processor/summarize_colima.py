#!/usr/bin/env python3
"""Phase 2, stage 2 — plain-language summaries + outcome per agenda item.

Reads the OCR text produced by `ocr_colima.py` and, for each session, asks an
LLM to (a) restate each agenda point in plain Spanish and (b) record its
outcome *only when the acta states it clearly*. Writes one JSON per acta to
`data/summaries/<id>.json`.

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
    "No uses signos de admiración, ni emoji, ni adjetivos de bombo. Frases completas."
)

INSTRUCCION = (
    "Primero redacta un 'resumen_sesion': UNA sola frase (máx. ~30 palabras), en "
    "lenguaje llano, que le diga a un vecino de qué trató esta sesión en conjunto — "
    "los asuntos de fondo que se decidieron, no el trámite. Nombra lo concreto "
    "(colonias, obras, licencias, montos) si aparece. No inventes; si la sesión sólo "
    "tuvo trámites o el texto no alcanza, dilo con sobriedad.\n\n"
    "Luego, para cada punto del órden del día, redacta:\n"
    "- resumen: una o dos frases en lenguaje llano sobre qué se puso a consideración. "
    "Nombra colonias, fraccionamientos o calles si el acta los menciona.\n"
    "- sentido: uno de exactamente estos valores, según lo que el acta declare: "
    "'aprobado', 'rechazado', 'aplazado', 'retirado', 'tramite' (puntos de mero "
    "procedimiento: lista de asistencia, quórum, lectura del órden, clausura), o "
    "'no_determinable' si el texto no permite afirmar el resultado.\n"
    "Responde SOLO con JSON válido, sin texto alrededor, con esta forma:\n"
    '{"resumen_sesion": "...", "puntos": [{"n": <entero>, "resumen": "...", "sentido": "..."}]}'
)

SENTIDOS = {"aprobado", "rechazado", "aplazado", "retirado", "tramite", "no_determinable"}


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
        out.append({
            "n": n,
            "numeral": by_n[n].get("numeral"),
            "resumen": (row.get("resumen") or "").strip(),
            "sentido": sentido if sentido in SENTIDOS else "no_determinable",
        })
    return resumen_sesion, out


def summarize_acta(acta: dict, ocr: dict, dry_run: bool) -> dict | None:
    messages = build_messages(acta, ocr["texto_completo"])
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
