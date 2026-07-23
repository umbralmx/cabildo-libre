#!/usr/bin/env python3
"""Phase 3 (L2) — attendance per session from the pase de lista.

Reads the OCR of each acta, isolates the roll-call sentence ("… manifestaron su
presencia …"), and assigns every member of the 2024-2027 cabildo one of:

    presente · remoto · falta_justificada · ausente · no_determinable

against the canonical roster in `data/regidores-2024-2027.json`. Writes one JSON
per acta to `data/asistencia/<id>.json`. No API — pure text over the existing OCR.

**Honesty (the project rule, applied here).** The roll call is OCR of a scanned,
stamped page and is noisy. Attendance is asserted only from what the acta states:

  * A member is `presente`/`remoto`/`falta_justificada`/`ausente` only when their
    name is found inside the clause the acta uses to declare that state.
  * A member the roll call does **not** legibly name is `no_determinable` — never
    silently marked absent. Absence of a name in a noisy scan is not evidence of
    absence from the session.
  * "licencia" in the agenda means a *commercial permit*, not a member on leave;
    only the roll-call region (not the agenda) is read, so those never leak in.

The roster is the cabildo as installed; if a session names someone outside it,
they are reported under `no_reconocidos` rather than forced onto a roster entry.

Usage:
    python3 processor/asistencia_colima.py                 # all OCR'd, pending
    python3 processor/asistencia_colima.py --id 2024-2027-54 --force
    python3 processor/asistencia_colima.py --dry-run       # print, don't write
"""

from __future__ import annotations

import argparse
import datetime
import difflib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OCR_DIR = ROOT / "data" / "ocr"
ASIST_DIR = ROOT / "data" / "asistencia"
ROSTER_JSON = ROOT / "data" / "regidores-2024-2027.json"

# Where the roll call begins and ends inside the OCR text. "manifest…" catches
# "manifestaron/manifestó su presencia"; the prefix `presenci`/`asistenci` tolerates
# OCR that clips the trailing letters ("presenci" for "presencia"). The roll call
# runs until quorum is declared. Anchoring here (not on the agenda item "Lista de
# asistencia") keeps permit/agenda text out of the region.
INICIO = re.compile(r"manifest\w*\s+su\s+(?:presenci|asistenci)\w*", re.I)
FIN = re.compile(r"segundo\s+punto|habiendo\s+qu[oó]rum", re.I)

# State clauses, searched in the *normalized* region. Order of the tuple is the
# search priority when two markers overlap (justified beats a bare "inasistencia"
# that is part of "justificaron su inasistencia").
CLAUSULAS = [
    ("remoto", re.compile(r"(?:via|manera|forma)\s+remota|remota")),
    ("falta_justificada", re.compile(r"justific")),
    ("ausente", re.compile(r"inasisten|no\s+asisti|ausen")),
]


def norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.lower())


def roll_call_region(texto: str) -> str:
    m = INICIO.search(texto)
    if not m:
        return ""
    tail = texto[m.end():]
    end = FIN.search(tail)
    return tail[: end.start()] if end else tail[:1500]


def clause_markers(region_n: str) -> list[tuple[int, str]]:
    """Positions in the normalized region where each state clause begins.
    'presente' is implicit before the first marker."""
    marks: list[tuple[int, str]] = []
    for estado, rx in CLAUSULAS:
        for m in rx.finditer(region_n):
            i = m.start()
            # A bare inasistencia/ausencia that is really "justificaron su
            # inasistencia" belongs to the justified clause, not absence.
            if estado == "ausente" and "justific" in region_n[max(0, i - 25): i]:
                continue
            marks.append((i, estado))
    return sorted(marks)


def estado_en(pos: int, marks: list[tuple[int, str]]) -> str:
    estado = "presente"
    for i, e in marks:
        if i <= pos:
            estado = e
        else:
            break
    return estado


def _apellido_tokens(member: dict) -> list[str]:
    """The first word of apellido1 and the last word of apellido2, normalized —
    e.g. 'Ríos'/'de la Mora' → ['rios', 'mora']."""
    aps = member["apellidos"]
    return [norm(aps[0]).split()[0], norm(aps[-1]).split()[-1]]


def distinctive_keys(roster: list[dict]) -> dict[str, list[str]]:
    """Pick, per member, the apellido token that is *unique* across the roster —
    so we can match on one legible token instead of a fragile pair. Only 'lópez'
    is shared (López Alonso, López Legorreta, Farías López); each of those still
    has a unique second token (Alonso / Legorreta / Farías) to key on."""
    freq: Counter[str] = Counter(tk for m in roster for tk in set(_apellido_tokens(m)))
    keys: dict[str, list[str]] = {}
    for m in roster:
        cand = _apellido_tokens(m)
        uniq = [tk for tk in cand if freq[tk] == 1]
        keys[m["id"]] = uniq or cand
    return keys


def _tok_match(tok: str, target: str) -> bool:
    """A region token matches a target apellido if one is a prefix of the other
    (OCR clips trailing letters: 'legorret' vs 'legorreta', 'vizcain' vs
    'vizcaino') or they are fuzzily close (letter swaps)."""
    if len(tok) >= 4 and len(target) >= 4 and (tok.startswith(target) or target.startswith(tok)):
        return True
    return difflib.SequenceMatcher(None, tok, target).ratio() >= 0.82


def find_member(tokens: list[tuple[int, str]], keys: list[str], variantes: list[str],
                region_n: str) -> int:
    """First position in the tokenized region matching one of the member's
    distinctive apellido tokens; -1 if the roll call doesn't legibly name them."""
    for pos, tok in tokens:
        if any(_tok_match(tok, k) for k in keys):
            return pos
    for v in variantes:  # fallback: a recorded OCR variant, matched as substring
        m = re.search(re.escape(norm(v)), region_n)
        if m:
            return m.start()
    return -1


# A person entry in the roll call: a title, then 2–5 Title-Case name words. Used
# to catch names the roll call declares that belong to *no* roster member — a
# suplente sitting in for a titular. Role words never start a real name entry.
_TITULOS = r"Mtr[oa]|Licda|Lic|Dra|Dr|Profr?a|Prof|Ing|Arq|LAE|C"
NAME_ENTRY = re.compile(
    rf"\b(?:{_TITULOS})\.\s*"
    r"([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ.]+){1,4})"
)
_STOP = {
    "regidor", "regidora", "regidores", "regidoras", "sindico", "sindica",
    "presidente", "presidenta", "municipal", "secretario", "secretaria",
    "ayuntamiento", "cabildo", "honorable", "pleno", "comision", "comisiones",
    "orden", "dia", "sesion", "estado", "gobierno", "colima",
}


_CONECTORES = {"de", "la", "del", "los", "las", "y", "e"}


def member_tokens(roster: list[dict]) -> dict[str, set[str]]:
    """Every meaningful name token (given names + apellidos) per member, so a
    roll-call entry can be recognized even when OCR gives only the given names
    ('Edgar Osiris') and drops or mangles the apellido."""
    mt: dict[str, set[str]] = {}
    for m in roster:
        words = norm(m["nombre"]).split() + [w for a in m["apellidos"] for w in norm(a).split()]
        mt[m["id"]] = {w for w in words if len(w) >= 3 and w not in _CONECTORES}
    return mt


def _recognized(cand: list[str], keys: dict[str, list[str]], mtoks: dict[str, set[str]]) -> bool:
    """A candidate name belongs to a roster member if it hits their unique
    apellido, or shares ≥2 name tokens with them (given-name-led fragments)."""
    for mid, member_toks in mtoks.items():
        if any(_tok_match(t, k) for t in cand for k in keys[mid]):
            return True
        overlap = sum(1 for t in cand if any(_tok_match(t, mt) for mt in member_toks))
        if overlap >= 2:
            return True
    return False


def unrecognized(region: str, keys: dict[str, list[str]], mtoks: dict[str, set[str]]) -> list[str]:
    """Names the roll call declares that match no roster member — i.e. a likely
    suplente. Reported verbatim (not forced onto a roster slot), per the rule of
    not inferring who a substitute stands in for."""
    out: list[str] = []
    seen: set[str] = set()
    for m in NAME_ENTRY.finditer(region):
        name = re.sub(r"\s+", " ", m.group(1)).strip(" .")
        toks = [norm(w) for w in name.split() if w]
        if not toks or toks[0] in _STOP:
            continue
        if _recognized(toks, keys, mtoks):
            continue
        key = " ".join(toks)
        if key not in seen:
            seen.add(key)
            out.append(name)
    return out


def extract(texto: str, roster: list[dict], keys: dict[str, list[str]],
            mtoks: dict[str, set[str]]) -> dict:
    region = roll_call_region(texto)
    region_n = norm(region)
    marks = clause_markers(region_n)
    tokens = [(m.start(), m.group()) for m in re.finditer(r"\w+", region_n)]

    estados: dict[str, str] = {}
    for member in roster:
        pos = find_member(tokens, keys[member["id"]], member.get("variantes_ocr", []), region_n)
        estados[member["id"]] = estado_en(pos, marks) if pos >= 0 else "no_determinable"

    # Only surface un-rostered names when the roster isn't fully accounted for
    # (someone is not present/remote) — a substitute implies a titular is out.
    # This keeps a garbled-but-present roster name from being mis-flagged.
    hay_vacante = any(e not in ("presente", "remoto") for e in estados.values())
    no_reconocidos = unrecognized(region, keys, mtoks) if hay_vacante else []

    resumen = {e: 0 for e in ("presente", "remoto", "falta_justificada", "ausente", "no_determinable")}
    for e in estados.values():
        resumen[e] += 1
    resumen["asistio"] = resumen["presente"] + resumen["remoto"]  # present, in person or remote
    resumen["no_reconocidos"] = len(no_reconocidos)

    return {
        "region_encontrada": bool(region),
        "resumen": resumen,
        "estados": estados,
        "no_reconocidos": no_reconocidos,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--id", help="one acta by id")
    ap.add_argument("--limit", type=int, help="process at most N pending actas")
    ap.add_argument("--force", action="store_true", help="re-extract even if cached")
    ap.add_argument("--dry-run", action="store_true", help="print, don't write")
    args = ap.parse_args()

    roster = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))["integrantes"]
    keys = distinctive_keys(roster)
    mtoks = member_tokens(roster)
    ASIST_DIR.mkdir(parents=True, exist_ok=True)

    ocr_ids = [args.id] if args.id else sorted(
        (p.stem for p in OCR_DIR.glob("*.json")),
        key=lambda s: int(s.rsplit("-", 1)[-1]) if s.rsplit("-", 1)[-1].isdigit() else 0,
    )
    pending = [i for i in ocr_ids
               if (OCR_DIR / f"{i}.json").exists()
               and (args.force or args.dry_run or not (ASIST_DIR / f"{i}.json").exists())]
    if args.limit:
        pending = pending[: args.limit]

    print(f"OCR'd: {len(ocr_ids)} | pendientes: {len(pending)} | roster: {len(roster)}")

    ok = 0
    for acta_id in pending:
        ocr = json.loads((OCR_DIR / f"{acta_id}.json").read_text(encoding="utf-8"))
        data = extract(ocr["texto_completo"], roster, keys, mtoks)
        r = data["resumen"]
        flag = "" if data["region_encontrada"] else "  ⚠ sin pase de lista legible"
        if data["no_reconocidos"]:
            flag += "  ⚠ suplente?: " + "; ".join(data["no_reconocidos"])
        print(f"[{acta_id}] asistió {r['asistio']}/{len(roster)} "
              f"(pres {r['presente']}, remoto {r['remoto']}, "
              f"justif {r['falta_justificada']}, ausente {r['ausente']}, "
              f"nd {r['no_determinable']}){flag}")
        if args.dry_run:
            continue
        out = {
            "id": acta_id,
            "esquema": 2,  # +no_reconocidos (suplentes named outside the roster)
            "generado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "roster": "regidores-2024-2027",
            **data,
        }
        (ASIST_DIR / f"{acta_id}.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        ok += 1

    if not args.dry_run:
        print(f"listo: {ok} actas con asistencia extraída")


if __name__ == "__main__":
    main()
