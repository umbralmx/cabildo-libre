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

**Long actas are read in overlapping windows, not truncated.** Sending only the
first 45K chars silently discarded three quarters of the term: the outcome of a
punto is recorded at the *end* of its discussion, so truncation produced
`no_determinable` on 68 % of the puntos of the actas it cut, and on 0 % of the
actas that fit whole (`docs/indicadores-revision.md` §1). An acta is now split
into overlapping windows, each summarized, and the per-punto records merged by
`fusionar_puntos()` — which prefers a *stated* outcome over an unread one and
unions the structured lists, never averaging or inventing. Each summary records
how much of its text was actually read (`lectura`), so coverage is auditable
rather than assumed.

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
import http.client
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

from limpieza import limpiar
from orden_del_dia import modificacion
from roster_match import build_index, emparejar

ROOT = Path(__file__).resolve().parent.parent
ACTAS_JSON = ROOT / "data" / "actas.json"
OCR_DIR = ROOT / "data" / "ocr"
SUMMARY_DIR = ROOT / "data" / "summaries"

# --- provider config (the only provider-specific surface) ---------------------
LLM_ENDPOINT = os.environ.get("LLM_ENDPOINT", "https://api.deepseek.com/chat/completions")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-v4-flash")
LLM_API_KEY_ENV = os.environ.get("LLM_API_KEY_ENV", "DEEPSEEK_API_KEY")

# One window's worth of acta text per request. This is a *context* limit, not a
# cost limit: at $0.14/1M input tokens the whole term costs under a dollar, so
# nothing is dropped — long actas are split across windows instead.
VENTANA_CHARS = 45000
SOLAPE_CHARS = 3000    # overlap, so a punto straddling a boundary is read whole
MAX_VENTANAS = 24      # ~1M chars; beyond this the acta is flagged, not silently cut

# A batch is dozens of long requests in a row, so a dropped or truncated response
# is a matter of when, not if. Without retries one flaky read kills the whole run
# (it did: a 25-acta pass died on the first acta with IncompleteRead).
LLM_MAX_INTENTOS = 4
LLM_BACKOFF_BASE = 6  # seconds, doubled per retry, plus jitter

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


def ventanas(texto: str) -> list[str]:
    """Split an acta into overlapping windows. The overlap matters: a punto whose
    discussion straddles a boundary would otherwise lose its outcome, which is the
    exact failure the truncation caused."""
    if len(texto) <= VENTANA_CHARS:
        return [texto]
    paso = VENTANA_CHARS - SOLAPE_CHARS
    trozos = [texto[i:i + VENTANA_CHARS] for i in range(0, len(texto), paso)]
    trozos = [t for t in trozos if t.strip()]
    return trozos[:MAX_VENTANAS]


def build_messages(
    acta: dict, ocr_text: str, ventana: tuple[int, int] = (1, 1), modificado: dict | None = None
) -> list[dict]:
    i, n = ventana
    agenda = "\n".join(
        f"{it['n']}. ({it.get('numeral') or '·'}) {it['texto']}"
        for it in acta["agenda_items"]
    )
    if n > 1:
        # The model must not guess at puntos it cannot see. Silence about a punto
        # is information (another window covers it); a fabricated outcome is not.
        contexto = (
            f"\n\nIMPORTANTE: este es el FRAGMENTO {i} de {n} del acta; el texto viene "
            "cortado al principio y al final. Reporta ÚNICAMENTE los puntos del órden "
            "del día de los que este fragmento hable. Omite por completo los puntos que "
            "no aparezcan aquí: otro fragmento los cubre. No deduzcas el resultado de un "
            "punto cuya votación no esté en este fragmento; para esos, si los incluyes, "
            "usa 'no_determinable'."
        )
        cabecera = f"=== TEXTO OCR DEL ACTA — FRAGMENTO {i} de {n} ==="
    else:
        contexto = ""
        cabecera = "=== TEXTO OCR DEL ACTA ==="
    # El órden del día de abajo viene del índice del portal: es el órden *previo*
    # a la sesión. Cuando el cabildo retira o incorpora asuntos —19 de las 78
    # actas del término— todo lo posterior recorre un lugar y esa numeración deja
    # de valer para el cuerpo del acta. Si cada ventana elige por su cuenta a cuál
    # numeración obedecer, `fusionar_puntos` une por `n` dos asuntos distintos:
    # es lo que produjo el conflicto del acta 48 punto 7. La regla debe ser una
    # sola y la misma en todas las ventanas: **manda el ordinal que el cuerpo del
    # acta escribe** ("SÉPTIMO PUNTO" → n=7), porque es el único que todas las
    # ventanas ven igual. Detección en `orden_del_dia.py`.
    numeracion = (
        "\n\nNUMERACIÓN — REGLA ÚNICA: el campo 'n' de cada punto debe salir del "
        "ordinal que el CUERPO DEL ACTA escribe ('PRIMER PUNTO' → 1, 'SÉPTIMO PUNTO' "
        "→ 7, 'DÉCIMO SEGUNDO PUNTO' → 12). El órden del día que te doy abajo es el "
        "previo a la sesión y sirve sólo de referencia temática. NUNCA numeres por "
        "esa lista si el acta usa otro ordinal: manda el acta."
    )
    if modificado:
        numeracion += (
            "\n\nATENCIÓN: en esta sesión el cabildo MODIFICÓ su órden del día "
            "(retiró y/o incorporó asuntos) antes de aprobarlo, así que el órden de "
            "abajo NO coincide con el del acta a partir del primer cambio. Guíate "
            "por el ordinal del acta y por el asunto, no por la posición en la lista."
        )
    user = (
        f"{INSTRUCCION}{numeracion}{contexto}\n\n"
        f"=== ÓRDEN DEL DÍA PREVIO (acta {acta['no_acta']}, {acta['fecha']}) ===\n{agenda}\n\n"
        f"{cabecera}\n{ocr_text}"
    )
    return [{"role": "system", "content": SISTEMA}, {"role": "user", "content": user}]


def _es_transitorio(e: BaseException) -> bool:
    """True for failures worth retrying: a dropped or truncated response, a
    timeout, a rate limit, or a provider-side 5xx. An auth or bad-request error
    is *not* transient — retrying it only burns the batch's time, so it raises."""
    if isinstance(e, urllib.error.HTTPError):
        return e.code == 429 or 500 <= e.code < 600
    return isinstance(e, (http.client.HTTPException, urllib.error.URLError,
                          TimeoutError, ConnectionError, json.JSONDecodeError))


def call_llm(messages: list[dict]) -> str:
    """The one provider-specific call. Returns the model's raw text response.
    Retries transient failures with exponential backoff; the caller sees either a
    response or the final exception (never a silently empty summary)."""
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

    for intento in range(1, LLM_MAX_INTENTOS + 1):
        req = urllib.request.Request(
            LLM_ENDPOINT, data=body, method="POST",
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {api_key}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except Exception as e:  # noqa: BLE001 — re-raised below unless transient
            if intento == LLM_MAX_INTENTOS or not _es_transitorio(e):
                raise
            espera = LLM_BACKOFF_BASE * 2 ** (intento - 1) + random.uniform(0, 3)
            print(f"  · {type(e).__name__}: {e} — reintento "
                  f"{intento}/{LLM_MAX_INTENTOS - 1} en {espera:.0f}s", flush=True)
            time.sleep(espera)
    raise AssertionError("unreachable")  # pragma: no cover


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
    except json.JSONDecodeError:
        raise ValueError("model did not return valid JSON")
    if not isinstance(payload, dict):
        raise ValueError("model did not return the expected JSON shape")
    # A window that covers none of the agenda legitimately returns no puntos —
    # that is silence about what it couldn't see, not a malformed answer.
    rows = payload.get("puntos") or []
    if not isinstance(rows, list):
        raise ValueError("model returned a non-list 'puntos'")

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


def _union(listas: list[list], clave) -> list:
    """Concatenate lists from several windows, dropping repeats. The overlap makes
    duplicates the norm, so dedup is required — but nothing is ever *merged*: two
    different amounts stay two amounts."""
    out, vistos = [], set()
    for lista in listas:
        for item in lista or []:
            k = clave(item)
            if k not in vistos:
                vistos.add(k)
                out.append(item)
    return out


# Merge precedence per field: values earlier in the tuple are *weaker* and lose to
# any later one. A window that only caught a punto in passing — in the agenda
# reading or the closing recap — tends to call it procedural; a window that read the
# discussion calls it what it was. So `tramite` yields to a stated outcome exactly
# as `no_determinable` does. (Acta 51 punto 18 was demoted this way: a Convenio de
# Hermanamiento approved by the cabildo, filed as mere procedure.)
DEBILES = {
    "sentido": ("no_determinable", "tramite"),
    "votacion": ("no_determinable",),
    "categoria": ("otro", "tramite"),
}


def fusionar_puntos(parciales: list[list[dict]]) -> tuple[list[dict], list[int]]:
    """Merge the per-punto records that each window produced.

    The governing rule: **a stated outcome beats a weaker reading.** A window that
    never saw a punto's vote reports `no_determinable`, and one that only glimpsed
    it reports `tramite`; neither may overwrite a window that read the decision
    (see `DEBILES`). Where two windows both state a real outcome and disagree, the
    majority wins (ties → the later window, since the vote is recorded at the end
    of the discussion) and the punto is reported as contested rather than silently
    resolved. A weak-vs-strong disagreement is *not* contested — the precedence
    settles it by rule, so `puntos_en_conflicto` stays what it should be: the puntos
    where two windows each read a decision and read it differently, which are the
    ones worth checking against the PDF. Lists are unioned; nothing is averaged.

    Returns (puntos, numeros_en_conflicto)."""
    por_n: dict[int, list[dict]] = {}
    for i, puntos in enumerate(parciales):
        for pt in puntos:
            por_n.setdefault(pt["n"], []).append({**pt, "_ventana": i})

    fusionados, conflictos = [], []
    for n in sorted(por_n):
        versiones = por_n[n]
        base = dict(versiones[-1])
        base.pop("_ventana", None)

        for campo, debiles in DEBILES.items():
            # Strongest tier that any window actually reported wins the field.
            for nivel in range(len(debiles), -1, -1):
                excluidos = set(debiles[:nivel])
                dichos = [v for v in versiones
                          if v.get(campo) is not None and v[campo] not in excluidos]
                if dichos:
                    break
            if not dichos:
                base[campo] = debiles[0]
                continue
            conteo = Counter(v[campo] for v in dichos)
            top = conteo.most_common(1)[0][1]
            empatados = [c for c, k in conteo.items() if k == top]
            # tie → the reading from the latest window that stated it
            base[campo] = next(v[campo] for v in reversed(dichos) if v[campo] in empatados)
            if campo == "sentido" and len(conteo) > 1:
                conflictos.append(n)

        # The window that read the outcome read the substance: prefer its prose.
        con_sentido = [v for v in versiones if v.get("sentido") not in (None, "no_determinable")]
        candidatos = [v.get("resumen", "") for v in (con_sentido or versiones)]
        base["resumen"] = max(candidatos, key=len, default="")

        base["colonias"] = _union([v.get("colonias") for v in versiones], lambda s: s.lower())
        base["obras"] = _union([v.get("obras") for v in versiones], lambda s: s.lower())
        base["montos"] = _union([v.get("montos") for v in versiones],
                                lambda m: (m.get("texto", "").lower(), m.get("valor_mxn")))
        for campo in ("votos_en_contra", "abstenciones"):
            base[campo] = _union([v.get(campo) for v in versiones],
                                 lambda p: (p.get("id") or p.get("nombre", "").lower()))
        for campo in ("beneficiario", "comision", "autor"):
            base[campo] = next((v[campo] for v in versiones if v.get(campo)), None)

        fusionados.append(base)
    return fusionados, sorted(set(conflictos))


def summarize_acta(acta: dict, ocr: dict, dry_run: bool) -> dict | None:
    # Feed the model the cleaned text: less structural noise fits more real
    # content per window and sharpens extraction. Raw stays as evidence.
    texto = limpiar(ocr["texto_completo"])
    trozos = ventanas(texto)
    n = len(trozos)
    # Si la sesión movió su órden del día, la numeración del índice ya no vale y
    # el prompt tiene que decirlo (ver `build_messages`). Es un parseo local, sin
    # costo ni red.
    modificado = modificacion(texto)

    if dry_run:
        print(f"[{acta['id']}] {len(texto):,} chars → {n} ventana(s)"
              f"{'  [órden del día modificado en sesión]' if modificado else ''}")
        print(build_messages(acta, trozos[0], (1, n), modificado)[1]["content"][:1500])
        return None

    parciales: list[list[dict]] = []
    resumen_sesion = ""
    fallidas = 0
    for i, trozo in enumerate(trozos, 1):
        if n > 1:
            print(f"  · ventana {i}/{n} ({len(trozo):,} chars)", flush=True)
        try:
            raw = call_llm(build_messages(acta, trozo, (i, n), modificado))
            rs, puntos = parse_summary(raw, acta)
        except (ValueError, KeyError, OSError, http.client.HTTPException) as e:
            # Losing one window of fourteen must not cost the whole acta. The gap
            # is subtracted from the coverage figure instead of being papered over.
            print(f"  ! ventana {i}/{n}: {type(e).__name__}: {e}; se omite", flush=True)
            fallidas += 1
            continue
        parciales.append(puntos)
        if not resumen_sesion:
            resumen_sesion = rs  # the session's framing lives in the first window
    if fallidas == n:
        raise ValueError(f"ninguna de las {n} ventanas pudo resumirse")

    puntos, conflictos = fusionar_puntos(parciales)
    if not puntos:
        raise ValueError("el modelo no devolvió ningún punto del órden del día")
    # Overlap means the windows double-count characters; what matters is whether
    # the whole acta was seen — true unless MAX_VENTANAS cut it or a window failed.
    paso = VENTANA_CHARS - SOLAPE_CHARS
    cubierto = min(len(texto), VENTANA_CHARS + (n - 1) * paso) - fallidas * paso
    return {
        "id": acta["id"],
        "no_acta": acta["no_acta"],
        "fecha": acta["fecha"],
        "periodo": acta["periodo"],
        "esquema": ESQUEMA,
        "modelo": LLM_MODEL,
        "fuente_texto": ocr["motor"],
        "generado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        # Coverage of the source text, so the dashboard can state how much of the
        # expediente was actually read instead of implying it was all of it.
        "lectura": {
            "chars_ocr": len(texto),
            "chars_leidos": max(cubierto, 0),
            "ventanas": n,
            "ventanas_fallidas": fallidas,
            "completa": fallidas == 0 and cubierto >= len(texto),
        },
        "puntos_en_conflicto": conflictos,
        # Queda anotado en el propio resumen: un lector del JSON tiene que poder
        # saber que la numeración del índice no rige aquí, sin ir a otro archivo.
        "orden_del_dia_modificado": bool(modificado),
        "resumen_sesion": resumen_sesion,
        "puntos": puntos,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--id", help="summarize a single acta by id")
    ap.add_argument("--ids", help="comma-separated acta numbers or ids (e.g. '3,7,48')")
    ap.add_argument("--solo-modificadas", action="store_true",
                    help="only actas whose órden del día was modified in session")
    ap.add_argument("--limit", type=int, help="process at most N pending actas")
    ap.add_argument("--force", action="store_true", help="re-summarize even if cached")
    ap.add_argument("--dry-run", action="store_true", help="print the prompt, no API call")
    args = ap.parse_args()

    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    actas = {a["id"]: a for a in json.loads(ACTAS_JSON.read_text(encoding="utf-8"))["actas"]}

    ocr_ids = [args.id] if args.id else sorted(p.stem for p in OCR_DIR.glob("*.json"))

    if args.ids:
        # Acepta "48" o "2024-2027-48": el número es lo que uno tiene a la mano
        # cuando lee la bitácora, y el id es lo que imprime el pipeline.
        querido = {s.strip() for s in args.ids.split(",") if s.strip()}
        ocr_ids = [i for i in ocr_ids if i in querido or i.rsplit("-", 1)[-1] in querido]

    if args.solo_modificadas:
        # La lista NO se escribe a mano: se deriva del propio OCR en cada corrida,
        # así que no puede quedar desfasada cuando entren actas nuevas. Es el
        # selector del arreglo de numeración (ver `orden_del_dia.py`).
        ocr_ids = [
            i for i in ocr_ids
            if modificacion(limpiar(
                json.loads((OCR_DIR / f"{i}.json").read_text(encoding="utf-8"))["texto_completo"]))
        ]
        print(f"órden del día modificado en sesión: {len(ocr_ids)} acta(s)")
    pending = [i for i in ocr_ids
               if i in actas and (args.force or not (SUMMARY_DIR / f"{i}.json").exists())]
    if args.limit:
        pending = pending[:args.limit]

    print(f"OCR'd actas: {len(ocr_ids)} | summaries pending: {len(pending)} | model: {LLM_MODEL}")

    ok = 0
    fallidas: list[str] = []
    for acta_id in pending:
        ocr = json.loads((OCR_DIR / f"{acta_id}.json").read_text(encoding="utf-8"))
        print(f"[{acta_id}] {actas[acta_id]['fecha']} …", flush=True)
        try:
            result = summarize_acta(actas[acta_id], ocr, args.dry_run)
        except (ValueError, KeyError, OSError, http.client.HTTPException) as e:
            # One acta the provider won't answer must not abort the batch: keep
            # its old summary (or none) and move on. Reported at the end.
            print(f"  ! {type(e).__name__}: {e}; skipping")
            fallidas.append(acta_id)
            continue
        if result is None:  # dry run
            continue
        (SUMMARY_DIR / f"{acta_id}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        n_det = sum(1 for p in result["puntos"] if p["sentido"] not in ("no_determinable", "tramite"))
        print(f"  → {len(result['puntos'])} puntos ({n_det} con sentido determinado)")
        ok += 1

    print(f"done: {ok} summarized this run")
    if fallidas:
        # Visible, not swallowed: these actas keep whatever summary they had, so a
        # partial pass can't be mistaken for a complete one.
        print(f"sin resumir ({len(fallidas)}): {', '.join(fallidas)}")


if __name__ == "__main__":
    main()
