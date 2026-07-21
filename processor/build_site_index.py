#!/usr/bin/env python3
"""Phase 2, stage 3 — compile the processed data into what the site loads.

Turns `data/summaries/*.json` and `data/ocr/*.json` into two payloads under
`site/`:

  - site/summaries.json — small, loaded eagerly. Attaches a plain-language
    resumen + sentido to each agenda item that has one.
  - site/fulltext.json — larger, loaded lazily (only when a reader runs a
    full-text search). One entry per OCR'd acta: its whole text.

Both are always written (empty objects if nothing is processed yet) so the
site's fetch never 404s. Runs after the OCR and summary stages; wired into
procesar.yml.

Usage: python3 processor/build_site_index.py
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OCR_DIR = ROOT / "data" / "ocr"
SUMMARY_DIR = ROOT / "data" / "summaries"
SITE = ROOT / "site"


def build_summaries() -> dict:
    resumenes = {}
    for f in sorted(SUMMARY_DIR.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        resumenes[d["id"]] = {
            "modelo": d["modelo"],
            "puntos": {str(p["n"]): {"resumen": p["resumen"], "sentido": p["sentido"]}
                       for p in d["puntos"] if p["resumen"]},
        }
    return {
        "generado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "resumenes": resumenes,
    }


def build_fulltext() -> dict:
    textos = {}
    for f in sorted(OCR_DIR.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        textos[d["id"]] = d["texto_completo"]
    return {
        "generado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "motor": "tesseract-spa",
        "textos": textos,
    }


def main() -> None:
    SITE.mkdir(parents=True, exist_ok=True)

    summaries = build_summaries()
    (SITE / "summaries.json").write_text(
        json.dumps(summaries, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    fulltext = build_fulltext()
    (SITE / "fulltext.json").write_text(
        json.dumps(fulltext, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    n_res = len(summaries["resumenes"])
    n_txt = len(fulltext["textos"])
    ft_mb = (SITE / "fulltext.json").stat().st_size / 1e6
    print(f"summaries.json: {n_res} actas con resúmenes")
    print(f"fulltext.json:  {n_txt} actas con texto completo ({ft_mb:.1f} MB)")


if __name__ == "__main__":
    main()
