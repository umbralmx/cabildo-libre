#!/usr/bin/env python3
"""Scraper for the Colima actas de cabildo index page.

Colima-specific by design (see CLAUDE.md): all knowledge about this page's
HTML quirks lives here so a future multi-city refactor only touches this file.

Reads the index page (live URL or a saved HTML file), parses every table row
into a structured record, and writes data/actas.json.

Stdlib only — no dependencies — so it runs unchanged on GitHub Actions.

Usage:
    python3 scraper/scrape_colima.py                # fetch live page
    python3 scraper/scrape_colima.py --html FILE    # parse a saved copy
    python3 scraper/scrape_colima.py --out PATH     # default: data/actas.json
"""

import argparse
import datetime
import json
import re
import sys
import unicodedata
import urllib.request
from html import unescape
from pathlib import Path

SOURCE_URL = "https://www.colima.gob.mx/portal2016/actas-de-cabildo/"
USER_AGENT = "Mozilla/5.0 (compatible; actas-abiertas-colima; +https://github.com/jballesterosc/cabildo-libre)"

MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

# Colima municipal terms begin in mid-October of the starting year. Used only
# to backfill the handful of rows whose período cell is blank.
TERM_STARTS = [2012, 2015, 2018, 2021, 2024]

ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def strip_tags(fragment: str) -> str:
    return unescape(re.sub(r"<[^>]+>", " ", fragment))


def roman_to_int(s: str) -> int | None:
    total, prev = 0, 0
    for ch in reversed(s.upper()):
        val = ROMAN_VALUES.get(ch)
        if val is None:
            return None
        total = total - val if val < prev else total + val
        prev = max(prev, val)
    return total if total > 0 else None


def parse_fecha(raw: str) -> str | None:
    """'13 mayo, 2026' -> '2026-05-13'. Returns None if blank/unparseable."""
    raw = raw.strip().lower()
    m = re.match(r"^(\d{1,2})\s+([a-záéíóúñ]+),?\s+(\d{4})$", raw)
    if not m:
        return None
    month = MONTHS.get(m.group(2))
    if not month:
        return None
    try:
        return datetime.date(int(m.group(3)), month, int(m.group(1))).isoformat()
    except ValueError:
        return None


def parse_no_acta(raw: str) -> tuple[str, int | None]:
    """Normalize '074' / '0070' / 'Acta 0003' -> canonical int; keep raw."""
    raw = raw.strip()
    m = re.search(r"(\d+)", raw)
    return raw, int(m.group(1)) if m else None


def parse_periodo(raw: str, fecha_iso: str | None) -> str | None:
    """Normalize '2021 - 2024' / '2018 -2021' -> '2021-2024'.

    A blank cell is backfilled from the session date using TERM_STARTS
    (terms change over in October).
    """
    m = re.search(r"(\d{4})\s*-\s*(\d{4})", raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    if fecha_iso:
        d = datetime.date.fromisoformat(fecha_iso)
        for start in reversed(TERM_STARTS):
            if d >= datetime.date(start, 10, 1) or d.year > start:
                return f"{start}-{start + 3}"
    return None


def split_agenda_items(text: str) -> list[dict]:
    """Split raw agenda text into numbered items.

    Numbering styles seen on the page: 'I.', 'I.-', bare 'I' at a line start,
    and a few old rows with no numerals at all (items separated only by long
    dash runs). An item's number can also continue mid-line right after the
    previous sentence. Candidate matches are validated against the expected
    sequence (the first item must be I or II — one agenda starts at II — and
    each later one exactly previous + 1), which rejects look-alikes such as
    the honorific 'C.' (C = 100) or the V in 'C.V.'.
    """
    candidates = []
    pattern = (
        r"(?<![A-Za-zÁÉÍÓÚÑ])([IVXLCDM]{1,8})\.-?\s+(?=[A-ZÁÉÍÓÚÑ«\"'])"
        r"|(?:^|\n)\s*([IVXLCDM]{1,8})\s+(?=[A-ZÁÉÍÓÚÑ«\"'])"
    )
    for m in re.finditer(pattern, text):
        numeral = m.group(1) or m.group(2)
        val = roman_to_int(numeral)
        if val:
            candidates.append((m.start(), m.end(), numeral, val))

    starts = []
    expected = None
    for cand in candidates:
        if expected is None and cand[3] in (1, 2):
            starts.append(cand)
            expected = cand[3] + 1
        elif expected is not None and cand[3] == expected:
            starts.append(cand)
            expected += 1

    items = []
    for i, (start, end, numeral, val) in enumerate(starts):
        tail = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        body = clean_agenda_text(text[end:tail])
        if body:
            items.append({"n": val, "numeral": numeral, "texto": body})

    if not items:
        # Old-format fallback: no numerals, items separated by dash runs.
        chunks = [clean_agenda_text(c) for c in re.split(r"-{6,}", text)]
        chunks = [c for c in chunks if c and not re.fullmatch(r"orden del d[ií]a", c, re.I)]
        items = [{"n": i + 1, "numeral": None, "texto": c} for i, c in enumerate(chunks)]

    # A few cells paste session minutes after the final 'Clausura' item;
    # trim that spillover (Phase 2 gets the real full text from the PDF).
    if items:
        m = re.match(r"(.*?\bClausura\b[^.]*\.)", items[-1]["texto"], re.S)
        if m and len(items[-1]["texto"]) - m.end() > 100:
            items[-1]["texto"] = m.group(1)
    return items


def clean_agenda_text(text: str) -> str:
    """Drop the dash-run filler and collapse whitespace."""
    text = re.sub(r"-{3,}", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip("- ").strip()


def parse_rows(html: str) -> list[dict]:
    table_m = re.search(
        r'<table class="table table-striped table-bordered dataTable".*?</table>',
        html, re.S,
    )
    if not table_m:
        sys.exit("ERROR: actas table not found — page structure changed?")

    raw_rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_m.group(0), re.S)[1:]
    records = []
    problems = []

    for idx, row in enumerate(raw_rows):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if len(tds) != 5:
            problems.append(f"row {idx}: expected 5 cells, got {len(tds)}")
            continue

        fecha_texto = re.sub(r"\s+", " ", strip_tags(tds[0])).strip()
        fecha = parse_fecha(fecha_texto)
        no_raw, no_acta = parse_no_acta(strip_tags(tds[1]))
        periodo = parse_periodo(strip_tags(tds[2]), fecha)

        body_m = re.search(r'<div class="panel-body">(.*?)</div>', tds[3], re.S)
        agenda_raw = strip_tags(body_m.group(1)) if body_m else ""
        agenda_items = split_agenda_items(agenda_raw)

        pdf_m = re.search(r"href=['\"]([^'\"]+)['\"]", tds[4])
        pdf_url = pdf_m.group(1).strip() if pdf_m else None

        if fecha is None and fecha_texto:
            problems.append(f"row {idx}: unparseable date {fecha_texto!r}")
        if no_acta is None:
            problems.append(f"row {idx}: unparseable acta number {no_raw!r}")
        if pdf_url is None:
            problems.append(f"row {idx}: no PDF link")

        records.append({
            "id": None,  # assigned after dedup below
            "fecha": fecha,
            "fecha_texto": fecha_texto or None,
            "no_acta": no_acta,
            "no_acta_texto": no_raw,
            "periodo": periodo,
            "agenda_items": agenda_items,
            "pdf_url": pdf_url,
            "orden_indice": idx,  # position on the source page (newest first)
        })

    # The source page lists a few sessions twice (same fecha, número and agenda,
    # sometimes with a second, wrong PDF link). Keep one row per session,
    # preferring the link that actually names the acta number.
    grouped: dict[tuple, list[dict]] = {}
    for rec in records:
        key = (rec["fecha"], rec["no_acta"], rec["periodo"],
               json.dumps(rec["agenda_items"], ensure_ascii=False))
        grouped.setdefault(key, []).append(rec)
    deduped = []
    for group in grouped.values():
        best = next(
            (r for r in group
             if r["no_acta"] is not None and r["pdf_url"]
             and str(r["no_acta"]) in re.sub(r"\D", " ", r["pdf_url"].rsplit("/", 1)[-1]).split()),
            group[0],
        )
        deduped.append(best)
    deduped.sort(key=lambda r: r["orden_indice"])
    records = deduped

    # Stable, human-readable ids: periodo + acta number, disambiguated when the
    # same number appears twice within a período (it happens on the source page).
    seen: dict[str, int] = {}
    for rec in records:
        base = f"{rec['periodo'] or 'sp'}-{rec['no_acta'] if rec['no_acta'] is not None else 'x'}"
        seen[base] = seen.get(base, 0) + 1
        rec["id"] = base if seen[base] == 1 else f"{base}-{seen[base]}"

    return records, problems


def summarize(records: list[dict], problems: list[str]) -> str:
    n_items = sum(len(r["agenda_items"]) for r in records)
    empty_agenda = sum(1 for r in records if not r["agenda_items"])
    no_fecha = sum(1 for r in records if not r["fecha"])
    periodos = {}
    for r in records:
        periodos[r["periodo"]] = periodos.get(r["periodo"], 0) + 1
    lines = [
        f"records: {len(records)}",
        f"agenda items: {n_items}",
        f"records with empty agenda: {empty_agenda}",
        f"records without date: {no_fecha}",
        f"periodos: {json.dumps(periodos, ensure_ascii=False)}",
    ]
    if problems:
        lines.append(f"problems ({len(problems)}):")
        lines += [f"  - {p}" for p in problems]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--html", help="parse a saved HTML file instead of fetching")
    ap.add_argument("--out", default="data/actas.json")
    ap.add_argument("--site-out", default="site/actas.json",
                    help="minified copy served by the static site ('' to skip)")
    args = ap.parse_args()

    html = Path(args.html).read_text(encoding="utf-8") if args.html else fetch(SOURCE_URL)
    records, problems = parse_rows(html)

    out = {
        "fuente": SOURCE_URL,
        "generado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "actas": records,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(summarize(records, problems))
    print(f"wrote {out_path} ({out_path.stat().st_size / 1e6:.1f} MB)")

    if args.site_out:
        site_path = Path(args.site_out)
        site_path.parent.mkdir(parents=True, exist_ok=True)
        site_path.write_text(
            json.dumps(out, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        print(f"wrote {site_path} ({site_path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
