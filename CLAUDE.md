# CLAUDE.md — Actas Abiertas (Cabildo Colima)

> Persistent project context for the coding agent. Read this before any task.
> **Roles:** PM & ideation = Claude (chat). Development, testing, validation = Fable.
> **Status (2026-07-20):** Phase 1 is **live** at https://umbralmx.github.io/cabildo-libre/
> (public repo `umbralmx/cabildo-libre`, Pages on, scheduled refresh running). X1 (legal)
> is still open — the site launched in attribution mode with the license claim softened.
> **Phase 2 is underway**, scoped to the current term (2024-2027, 74 actas): a two-stage
> processing pipeline in `processor/` — **Tesseract OCR** (free) + **DeepSeek summaries**
> (text-only, ~$1/term). Engine spike and cost table in `docs/phase2-ocr-spike.md`.

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

**Cost note:** Phase 1 has effectively zero running cost — confirmed, it is static files plus a scheduled Action. **Phase 2's cost estimate changed:** it is no longer "just summaries". Every acta needs OCR *before* any summary, and the corpus is 636 sessions across 5 terms, not ~75. Scope Phase 2 to the current term first.

---

## Roadmap

| Phase | Name | Scope |
|---|---|---|
| **1** | The Index | Static site: **search bar + browsable session timeline** over agenda text. **Built and verified locally 2026-07-19/20; not yet public** (gated on X1 + X2). |
| **2** | The Deepening *(in progress)* | **OCR the scanned PDFs** (Tesseract) + plain-language summaries with outcome per agenda item (DeepSeek). Scoped to term 2024-2027 first. Pipeline built in `processor/`; site integration (full-content search + summary display) pending. |
| **3** | Trends & Scale | Trend dashboards (licencias, fraccionamientos, budgets per quarter) + multi-municipality abstraction. |

---

## Phase 1 backlog

Tasks are PM-level with acceptance criteria (`✓`). Implementation choices are Fable's.
**Status as of 2026-07-20: A, B and C are done; X1 and X2 are open and gate launch.**

### Epic A — Data acquisition ✅

- **A1 — Scrape the index into structured records.** ✅ `scraper/scrape_colima.py`, stdlib only.
  ✓ 640 rows → **636 sessions / 6,992 agenda items**, no manual cleanup.
- **A2 — Handle the messy bits.** ✅ All absorbed: numbering variants, three período spellings + one blank, four agenda numbering styles, dash-run separators, spilled minutes text, 4 duplicated sessions (deduped), and a **numbering gap in the source itself** (acta 76/2017 runs VI→VIII). Full rules in `docs/metodologia.md` §3.
- **A3 — [EARLY SPIKE] Verify PDF text-extractability.** ✅ **Result inverted the plan** — see `docs/a3-spike.md`. ~100% of actas need OCR.

### Epic B — Search & interface ✅

- **B1 — Static scaffold + browser-side search index.** ✅ In-memory over ~7k items, accent/case-folded, no dependencies.
  ✓ Verified: "carsol" → acta 71, punto IX, 15 abril 2026, linking to the PDF.
- **B2 — Combined interface.** ✅ Search + results, or year-grouped timeline expanding to full agendas.
- **B3 — Result view.** ✅ Date, acta number, punto, período, highlighted match, PDF link.
- **B4 — Filters.** ✅ Período + date range, applying to both timeline and results.
- **B5 — Design pass against the Umbral brand system.** ✅ *(added 2026-07-20)* Signal budget, type scale, 8px spacing, KPI stat row, table spec for the timeline, self-hosted fonts, a11y. Recorded in `docs/diseno.md`.

### Epic C — Deploy & refresh ✅ *(scaffolded, not yet public)*

- **C1 — Deploy** with a scheduled GitHub Action to re-scrape. ✅ Workflow written; **target agreed: `umbralmx/cabildo-libre` → https://umbralmx.github.io/cabildo-libre/** (project page, own repo). Not yet pushed: repo doesn't exist on GitHub yet and `gh` isn't authenticated locally.
  ✓ *Pending:* create repo, push, enable Pages (Source: GitHub Actions), trigger first run.

### Cross-cutting — validate early

- **X1 — Legal check.** ⚠️ **Reviewed 2026-07-20 → `docs/x1-terminos-legal.md`. Not a clean go.** The portal's T&C prohibit reproduction, distribution and public communication of its contents except for private use, research or study. There are serious counterarguments (official texts aren't copyrightable under LFDA art. 14; actas are transparency-obligated public information), but **this needs a human decision and ideally counsel.** Interim mitigation already applied: we no longer claim CC BY 4.0 over the source text, only over our own structuring work.
- **X2 — Hosting identity.** Partially resolved: `umbralmx.github.io/cabildo-libre/` is the free path and needs no purchase. A memorable domain is still an open preference. *(You)*

---

## Open items & checkpoints

- **X1 is now the real blocker** and it is not a formality. Cheap parallel moves: a formal transparency request to the Ayuntamiento, and a consult with R3D or Artículo 19 México. Options table in `docs/x1-terminos-legal.md` §5.
- **"Decision outcome" is a Phase 2 concept.** Phase 1 shows what was *on the agenda*; confirming *approved vs. tabled* depends on OCR + PDF parsing. The site states this limitation explicitly in its methodology section and in the empty-search state — keep it that way.
- **Phase 2 needs a scoping decision before any code:** OCR engine (Tesseract `spa` on Actions = free/slow/medium quality on stamped, signed scans; vs. a vision model = one-time cost per acta, cached) and corpus scope (all 636 actas vs. current term's 74). Do a small OCR quality spike on 3 actas of different vintages before committing.
- **Watch for source drift.** The scraper prints a control summary each run (records, items, empty agendas, problems). If those numbers move oddly after a scheduled run, the page's HTML likely changed.
- **Link rot is the ayuntamiento's, not ours** — but a periodic link check is worth adding in Phase 2/3.
- **Checkpoint cadence:** A1–A3 review ✅ done · B1–B2 review ✅ done · **pre-deploy review ← we are here**, blocked on X1.

---

## Next steps (2026-07-20)

**Done since last update:** Phase 1 is public (`umbralmx/cabildo-libre`, Pages live). Repo metadata set. Font path bug fixed. Phase 2 pipeline built (`processor/`) and OCR proven on 3 current-term actas.

**For the maintainer (human-only):**
1. **Decide X1.** Read `docs/x1-terminos-legal.md`. The site is already public in attribution mode, so this is now about response posture, not gating — start a transparency request and/or an R3D / Artículo 19 consult.
2. **Add the `DEEPSEEK_API_KEY` secret** to `umbralmx/cabildo-libre` (Settings → Secrets → Actions) so the Phase 2 `procesar.yml` workflow can run summaries. Without it, OCR still runs; summaries skip.
3. **Confirm X2** — keep `umbralmx.github.io/cabildo-libre/` or buy a domain (add a `CNAME`).

**Ready for the agent:**
4. Once the secret exists: trigger `procesar.yml` (workflow_dispatch) to OCR + summarize a first batch of the term; verify output quality on real DeepSeek summaries (this is the one thing not yet proven end-to-end — no key was available at build time).
5. **Site integration for Phase 2** ✅ *(done 2026-07-20)*: summaries render under each agenda item (timeline + results) with a `sentido` label and an AI/OCR disclaimer; lazy full-content search over `data/ocr/` with honest coverage; `processor/build_site_index.py` compiles `site/summaries.json` + `site/fulltext.json` (wired into `procesar.yml`). Section-number brand flourish added. Verified by a headless render smoke-test — **not yet a visual pass** (browser tool was down); eyeball the live page.
6. Watch the OCR text cap: `summarize_colima.py` sends the first 45K chars/acta — fine for most, but very large actas (e.g. acta 74, 108pp) get truncated. Revisit if outcomes on late pages get missed.

---

## Documentation map

| File | What it holds |
|---|---|
| `CLAUDE.md` *(this file)* | Project context, scope, backlog, status |
| `docs/metodologia.md` | **How the data is produced** — pipeline, parsing rules, editorial decisions, known gaps, how to reproduce |
| `docs/a3-spike.md` | The OCR spike: evidence that the PDFs are scans |
| `docs/phase2-ocr-spike.md` | Phase 2 engine spike: Tesseract vs vision, the DeepSeek decision, cost table |
| `processor/README.md` | **How Phase 2 runs** — the OCR + summary stages, deps, provider-swap, honesty rules |
| `docs/x1-terminos-legal.md` | T&C findings, risk, and options — **read before launching** |
| `docs/diseno.md` | How the Umbral brand system was applied, and deliberate deviations |
| `data/SOURCE.md` | Dataset provenance, caveats, licensing position |
| `README.md` | Orientation for anyone landing in the repo |

---

## Conventions for the agent

- Keep the Colima-specific scraping logic isolated (one module/file) so Phase 3 generalization is a refactor, not a rewrite — but **do not build the multi-city abstraction now.**
- Prefer boring, well-supported static tooling over clever infra. The maintainer inherits this; it must stay runnable with zero ops.
- When a task is ambiguous, surface the question at the next checkpoint rather than guessing at scope.
- **Never fill a gap in the source by inference.** Missing dates, missing agendas, skipped numerals and dead links stay visible in the data and, where it matters, on screen. The one exception (backfilling a blank período from the session date) is documented in `docs/metodologia.md` §3.3.
- **Follow the brand system in `assets/`** for anything user-facing; record interpretation calls in `docs/diseno.md` rather than drifting silently.