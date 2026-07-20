# CLAUDE.md — Actas Abiertas (Cabildo Colima)

> Persistent project context for the coding agent. Read this before any task.
> **Roles:** PM & ideation = Claude (chat). Development, testing, validation = Fable.
> **Status (2026-07-19):** Phase 1 **built and verified locally** — scraper, data, site, and
> deploy workflow are done (see backlog checkmarks below). Launch is gated on X1 (legal
> note) and X2 (URL), plus pushing to GitHub and enabling Pages. Phase 2 brief pending;
> its key input changed: **the acta PDFs are scans → OCR required** (`docs/a3-spike.md`).

---

## What this project is

A searchable, plain-language public window into municipal council decisions, starting with **Colima**.

Municipal *actas de cabildo* record what a city council discussed and approved — budgets, public works, land-use changes, licenses. Colima publishes them as a **wall of PDFs** with no search, no structure, and no summaries. A resident who wants a simple answer — *"when was the project in my neighborhood approved?"* — has to open and skim dozens of documents. The data isn't secret; it's **unnavigable**. This project fixes the navigability.

**Source:** https://www.colima.gob.mx/portal2016/actas-de-cabildo/

**References for the ambition:** [citymeetings.nyc](https://citymeetings.nyc/) (semantic, plain-language navigation) and document-browser tools — adapted to **text-PDF actas** rather than video transcripts.

---

## Hard constraints (do not violate)

- **No server. No local hosting.** The maintainer cannot run or pay for a persistent backend. Everything must be static + free-tier.
- **Separate processing from serving.** Processing is heavy/occasional/batch; serving is light/always-on/static. Nothing may require a live backend at request time.
- **Search runs in the user's browser** (e.g. Pagefind or a prebuilt client-side index). No search server, no database.
- **Colima first.** Build Colima well; do **not** over-abstract for multi-municipality yet. Generalization is Phase 3. Avoid premature generality that slows the first win.

---

## Prioritized accountability jobs (agreed ranking)

1. **Finding decisions** — search & lookup. The spine of the product.
2. **Explaining decisions** — plain-language summaries. The differentiator. (Phase 2)
3. **Tracking trends** — dashboards over time. Deferred. (Phase 3)

---

## Key findings from the source (these shape everything)

- **The agenda (órden del día) is already plain HTML text on the index page** — *not* locked inside the PDFs. Each session lists its numbered items as readable text. → **Phase 1 search was built without opening a single PDF.** Confirmed in practice: 636 sessions, 6,984 agenda items parsed from the index alone.
- **~~The acta PDFs appear to be text-based~~ — DISPROVEN by the A3 spike (2026-07-19).** All sampled PDFs (2016–2026) are **scanner output with zero extractable text** (image-only pages, no fonts; producers are literal office scanners). The `_opt`/`_compressed` suffixes meant file compression (iLovePDF), not digital text. → **Phase 2 requires OCR on ~100% of actas.** Details and options in `docs/a3-spike.md`.
- **The corpus is 5 terms (2012–2026), not one.** 636 sessions after dedup — far more than the ~75-actas-per-term planning figure. Phase 2 should probably scope OCR/summaries to the current término (2024-2027, 74 actas) first.
- **Some source links are dead.** Part of the 2013–2014 PDFs (old `portal2014` paths) 404 on the ayuntamiento's server. We link them anyway (the rot is theirs), but a periodic link check belongs in Phase 2/3.

**Two data tiers:**
- **Tier 1** — agenda text, already available on the index page → tells you *what was on the table*. **Phase 1 ships this.**
- **Tier 2** — full PDF text → tells you *what was decided and discussed*. **Phase 2 layers this in.**

---

## Architecture

```
SCRAPE ─▶ PROCESS ─▶ PUBLISH ─▶ SERVE
(batch, occasional, free)        (static, always-on, free)
```

- **Scrape + process** — runs on GitHub Actions (free, scheduled compute). Extracts agenda text (Phase 1) and PDF text (Phase 2) into static JSON.
- **Publish** — generated JSON / search index is committed to the repo. No database.
- **Serve** — static site on GitHub Pages or Cloudflare Pages (free). Client-side search.

**Cost note:** Phase 1 has effectively zero running cost. The only variable cost is Phase 2 LLM summaries — one-time per acta, cached permanently, trivial at ~75 actas per term.

---

## Roadmap

| Phase | Name | Scope |
|---|---|---|
| **1** | The Index *(current)* | Live static site: **search bar + browsable session timeline** over agenda text. Solves the original frustration on its own. |
| **2** | The Deepening | Extract PDF text; attach plain-language summaries to each agenda item + its outcome; full-content search. |
| **3** | Trends & Scale | Trend dashboards (licencias, fraccionamientos, budgets per quarter) + multi-municipality abstraction. |

---

## Phase 1 backlog

Tasks are PM-level with acceptance criteria (`✓`). Implementation choices are Fable's.

### Epic A — Data acquisition

- **A1 — Scrape the index into structured records.** Fields: `fecha`, `no_acta`, `período`, `agenda_items[]`, `pdf_url`.
  ✓ Every row on the page becomes one clean JSON record, agenda split into individual numbered items.
- **A2 — Handle the messy bits.** Inconsistent numbering (`074` vs `0070` vs `051`), dashed separators inside agenda text, duplicate dates (two actas on 14 marzo 2025).
  ✓ Parser survives all current rows with no manual cleanup.
- **A3 — [EARLY SPIKE] Verify PDF text-extractability** on 5–8 actas spread across the date range.
  ✓ We know the % of actas needing OCR. Run this early — it de-risks Phase 2 cheaply.

### Epic B — Search & interface

- **B1 — Static scaffold + browser-side search index** over agenda text.
  ✓ Typing "CARSOL CHEVROLET" returns acta #71, item IX, dated 15 abril 2026, linking to the PDF.
- **B2 — Combined interface: search bar + results list AND a browsable session timeline** (agreed primary interaction).
  ✓ A resident can either search a keyword or scroll the timeline, and reach a source PDF in two clicks.
- **B3 — Result view:** date, acta number, matching agenda item highlighted, link to source PDF.
  ✓ Match context is legible at a glance without opening the PDF.
- **B4 — Filters:** date range and período. (Theme filter deferred to Phase 2.)
  ✓ Date-range filter narrows timeline and results correctly.

### Epic C — Deploy & refresh

- **C1 — Deploy** to GitHub Pages / Cloudflare Pages with a scheduled GitHub Action to re-scrape.
  ✓ Site is live at a public URL and refreshes automatically when new actas are published.

### Cross-cutting — validate early

- **X1 — Legal check.** Review the site's *Términos y Condiciones* (linked on the actas page) to confirm scraping public actas is within terms. *(You + Claude)*
  ✓ A short written go/no-go note. Needed before public launch, not before development.
- **X2 — Hosting identity.** Memorable domain vs. free subdomain for v1. *(You)*
  ✓ A URL is chosen so C1 can ship.

---

## Open items & checkpoints

- **Run A3 first.** The OCR spike is the cheapest way to de-risk Phase 2 — even though it's Phase-2-facing.
- **"Decision outcome" is a Phase 2 concept.** Phase 1 shows what was *on the agenda*; confirming *approved vs. tabled* depends on PDF parsing. Flag any acta where agenda ≠ outcome as a design case.
- **Legal (X1)** gates public launch, not development.
- **Suggested checkpoint cadence:** short review after A1–A3 (is the data clean?) → after B1–B2 (does search actually answer the neighborhood question?) → pre-deploy.

---

## Conventions for the agent

- Keep the Colima-specific scraping logic isolated (one module/file) so Phase 3 generalization is a refactor, not a rewrite — but **do not build the multi-city abstraction now.**
- Prefer boring, well-supported static tooling over clever infra. The maintainer inherits this; it must stay runnable with zero ops.
- When a task is ambiguous, surface the question at the next checkpoint rather than guessing at scope.