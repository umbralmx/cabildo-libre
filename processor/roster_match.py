#!/usr/bin/env python3
"""Emparejar un nombre suelto contra el roster del cabildo.

El resumidor recibe del modelo nombres de regidores (quién votó en contra, quién
se abstuvo, quién presentó el dictamen) y necesita mapearlos a un id del roster
para poder agregarlos por persona. Reusa la misma lógica tolerante a OCR que
`asistencia_colima.py`: empareja por el apellido *único* de cada integrante o por
solape de ≥2 tokens de nombre, con tolerancia a truncamiento y erratas.

Honestidad: si un nombre no casa con nadie con confianza, devuelve `None` — no se
fuerza a un integrante. Un disidente que no está en el roster (un suplente) queda
con id `None` y su nombre textual, no se le atribuye el voto a un titular.
"""

from __future__ import annotations

import difflib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROSTER_JSON = ROOT / "data" / "regidores-2024-2027.json"

_CONECTORES = {"de", "la", "del", "los", "las", "y", "e"}


def _norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s)


def _tok_match(tok: str, target: str) -> bool:
    if len(tok) >= 4 and len(target) >= 4 and (tok.startswith(target) or target.startswith(tok)):
        return True
    return difflib.SequenceMatcher(None, tok, target).ratio() >= 0.82


def _apellido_tokens(member: dict) -> list[str]:
    aps = member["apellidos"]
    return [_norm(aps[0]).split()[0], _norm(aps[-1]).split()[-1]]


def build_index(roster: list[dict] | None = None) -> dict:
    """Precompute, per member: the unique apellido key(s) and the full name-token
    set. Pass once, reuse across many `emparejar` calls."""
    if roster is None:
        roster = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))["integrantes"]
    freq: Counter[str] = Counter(tk for m in roster for tk in set(_apellido_tokens(m)))
    keys, toks = {}, {}
    for m in roster:
        cand = _apellido_tokens(m)
        uniq = [tk for tk in cand if freq[tk] == 1]
        keys[m["id"]] = uniq or cand
        words = _norm(m["nombre"]).split() + [w for a in m["apellidos"] for w in _norm(a).split()]
        toks[m["id"]] = {w for w in words if len(w) >= 3 and w not in _CONECTORES}
    return {"keys": keys, "toks": toks}


def emparejar(nombre: str, index: dict) -> str | None:
    """id del integrante que mejor casa con `nombre`, o None si ninguno con
    confianza. Prioriza el apellido único; desempata por solape de tokens."""
    cand = [t for t in _norm(nombre).split() if len(t) >= 2 and t not in _CONECTORES]
    if not cand:
        return None
    mejor, mejor_score = None, 0
    for mid, member_keys in index["keys"].items():
        apellido_hit = any(_tok_match(t, k) for t in cand for k in member_keys)
        overlap = sum(1 for t in cand if any(_tok_match(t, mt) for mt in index["toks"][mid]))
        if not apellido_hit and overlap < 2:
            continue
        score = overlap + (2 if apellido_hit else 0)
        if score > mejor_score:
            mejor, mejor_score = mid, score
    return mejor
