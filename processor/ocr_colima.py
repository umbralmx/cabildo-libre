#!/usr/bin/env python3
"""Phase 2, stage 1 — OCR the scanned acta PDFs into text.

The actas are scanner output with no text layer (see docs/a3-spike.md), so the
only way to full-text is optical character recognition. This stage rasterizes
each page and runs Tesseract (`spa`); it is the free, reproducible half of the
hybrid pipeline. The plain-language summaries come later, in
`summarize_colima.py`, over the text this stage produces.

Scoped to a single período by default (Phase 2 targets the current term first —
see CLAUDE.md). Cache-aware and batchable so GitHub Actions can fill in the
corpus a few actas per run instead of in one 2 GB pass.

Output: one JSON per acta in `data/ocr/<id>.json`.

Dependencies (not stdlib — this stage is the heavy, occasional half):
  - PyMuPDF (`pip install pymupdf`) to rasterize pages
  - the `tesseract` binary with Spanish data
      · Debian/Actions: apt-get install -y tesseract-ocr tesseract-ocr-spa
      · macOS:          brew install tesseract tesseract-lang

Usage:
    python3 processor/ocr_colima.py                     # current term, all pending
    python3 processor/ocr_colima.py --limit 10          # next 10 pending (CI batch)
    python3 processor/ocr_colima.py --periodo 2021-2024
    python3 processor/ocr_colima.py --id 2024-2027-1 --force
"""

from __future__ import annotations

import argparse
import datetime
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parent.parent
ACTAS_JSON = ROOT / "data" / "actas.json"
OCR_DIR = ROOT / "data" / "ocr"
PDF_CACHE = ROOT / "data" / "raw" / "pdfs"  # git-ignored; PDFs are never re-hosted
DEFAULT_PERIODO = "2024-2027"
DPI = 200
USER_AGENT = "Mozilla/5.0 (compatible; actas-abiertas-colima)"


def tesseract_langs() -> set[str]:
    out = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True)
    return {l.strip() for l in out.stdout.splitlines()[1:]}


def preflight() -> None:
    if not shutil.which("tesseract"):
        sys.exit("ERROR: `tesseract` not found. Install tesseract-ocr + the `spa` "
                 "language data (see this file's header).")
    if "spa" not in tesseract_langs():
        sys.exit("ERROR: Tesseract is missing the Spanish (`spa`) language data.")


def fetch_pdf(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return True
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=180) as r, open(dest, "wb") as f:
            shutil.copyfileobj(r, f)
        return True
    except Exception as e:  # dead links are the ayuntamiento's; skip, don't crash
        print(f"  ! download failed ({e}); skipping")
        dest.unlink(missing_ok=True)
        return False


def ocr_page(page: "fitz.Page") -> str:
    """Rasterize one page and pipe the PNG straight into Tesseract via stdin."""
    png = page.get_pixmap(dpi=DPI).tobytes("png")
    proc = subprocess.run(
        ["tesseract", "stdin", "stdout", "-l", "spa"],
        input=png, capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace")[:200])
    return proc.stdout.decode("utf-8", "replace")


def ocr_acta(acta: dict) -> dict | None:
    pdf_path = PDF_CACHE / f"{acta['id']}.pdf"
    if not fetch_pdf(acta["pdf_url"], pdf_path):
        return None
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"  ! cannot open PDF ({e}); skipping")
        return None

    pages = []
    for i, page in enumerate(doc):
        text = ocr_page(page).strip()
        pages.append({"n": i + 1, "texto": text})
        print(f"  page {i + 1}/{len(doc)}  ({len(text)} chars)", end="\r")
    doc.close()
    print()

    return {
        "id": acta["id"],
        "no_acta": acta["no_acta"],
        "fecha": acta["fecha"],
        "periodo": acta["periodo"],
        "pdf_url": acta["pdf_url"],
        "motor": "tesseract-spa",
        "dpi": DPI,
        "generado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "n_paginas": len(pages),
        "paginas": pages,
        "texto_completo": "\n".join(p["texto"] for p in pages),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--periodo", default=DEFAULT_PERIODO, help="'' for all términos")
    ap.add_argument("--id", help="OCR a single acta by id")
    ap.add_argument("--limit", type=int, help="process at most N pending actas")
    ap.add_argument("--force", action="store_true", help="re-OCR even if cached")
    args = ap.parse_args()

    preflight()
    OCR_DIR.mkdir(parents=True, exist_ok=True)
    PDF_CACHE.mkdir(parents=True, exist_ok=True)

    actas = json.loads(ACTAS_JSON.read_text(encoding="utf-8"))["actas"]
    if args.id:
        actas = [a for a in actas if a["id"] == args.id]
    elif args.periodo:
        actas = [a for a in actas if a["periodo"] == args.periodo]
    actas = [a for a in actas if a["pdf_url"]]

    pending = [a for a in actas
               if args.force or not (OCR_DIR / f"{a['id']}.json").exists()]
    done_already = len(actas) - len(pending)
    if args.limit:
        pending = pending[:args.limit]

    print(f"scope: {len(actas)} actas | already OCR'd: {done_already} | "
          f"processing now: {len(pending)}")

    ok = 0
    for a in pending:
        print(f"[{a['id']}] {a['fecha']}")
        result = ocr_acta(a)
        if result is None:
            continue
        out = OCR_DIR / f"{a['id']}.json"
        out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        chars = len(result["texto_completo"])
        print(f"  → {out.relative_to(ROOT)}  ({result['n_paginas']} pp, {chars:,} chars)")
        ok += 1

    remaining = len(actas) - done_already - ok
    print(f"done: {ok} OCR'd this run | {remaining} still pending in scope")


if __name__ == "__main__":
    main()
