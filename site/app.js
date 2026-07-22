/* Actas Abiertas — client-side search + timeline over site/actas.json.
   No dependencies: the whole dataset (~7k agenda items) filters in-memory. */

"use strict";

const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
  "agosto", "septiembre", "octubre", "noviembre", "diciembre"];

/* A point is "substantive" if it decides something; "procedural" if it is the
   scaffolding every session repeats (roll call, quorum, reading the agenda,
   approving previous minutes, recess, closing). Used only for visual
   hierarchy — the full text is always rendered either way. */
const SUSTANTIVO = /dictamen|punto de acuerdo|iniciativa|convenio|reglamento|presupuesto|propuesta|autoriza|aprueba la|informe/i;
const PROCEDIMIENTO = /^(lista de (asistencia|presentes)|declaraci[oó]n de qu[oó]rum|instalaci[oó]n legal|lectura (y aprobaci[oó]n[^.]*acta|del [oó]rden|del orden)|receso|clausura|asuntos generales)/i;

const $ = (sel) => document.querySelector(sel);

const state = {
  actas: [], q: "", periodo: "", desde: "", hasta: "",
  summaries: {},      // acta id → { modelo, puntos: { n → {resumen, sentido} } }
  fulltext: null,     // acta id → OCR text; loaded once, on first search
  fulltextLoading: false,
  _ftFolded: {},
};

/* Per-character accent/case folding that preserves string indices, so match
   positions found in the folded text map 1:1 back onto the original. */
const foldCache = new Map();
function foldChar(ch) {
  let f = foldCache.get(ch);
  if (f === undefined) {
    f = ch.normalize("NFD")[0].toLowerCase();
    foldCache.set(ch, f);
  }
  return f;
}
function fold(s) {
  let out = "";
  for (const ch of s) out += foldChar(ch);
  return out;
}

function esProcedural(texto) {
  return !SUSTANTIVO.test(texto) && PROCEDIMIENTO.test(texto);
}

/* Phase 2 summaries. `sentido` renders as a restrained mono label — monochrome
   by default so it never competes with the search-match signal; alert only for
   the rare, notable rejection; procedural 'tramite' points show no label. */
const SENTIDO_LABEL = {
  aprobado: "aprobado", rechazado: "rechazado",
  aplazado: "aplazado", retirado: "retirado",
  no_determinable: "sin resultado registrado en el acta",
};
function sentidoHTML(sentido) {
  if (!sentido || sentido === "tramite") return "";
  const label = SENTIDO_LABEL[sentido] || sentido;
  const cls = sentido === "rechazado" ? " sd-alert"
    : sentido === "no_determinable" ? " sd-open" : "";
  return `<span class="sentido${cls}">${esc(label)}</span>`;
}
function resumenDe(actaId, n) {
  return state.summaries[actaId]?.puntos?.[n] ?? null;
}

/* Nearly every point opens with the same formula ("Lectura, discusión y
   aprobación en su caso, del Dictamen que autoriza…"), which buries the
   subject. Strip that lead-in for the one-line session label only — the
   untouched text is always shown in the expanded agenda and in the data. */
const LEAD_INS = [
  /^lectura[^,]*,\s*/i,
  /^(discusi[oó]n\s*y\s*)?aprobaci[oó]n[^,]*,\s*/i,
  /^en su caso,?\s*/i,
  /^d(el|e la|e los|e las)\s+/i,
  /^(dictamen|punto de acuerdo|iniciativa|propuesta)\s+/i,
  /^(que|por el que|por la que|mediante el cual)\s+(se\s+)?/i,
];

function tituloCorto(texto) {
  let t = texto;
  for (const re of LEAD_INS) t = t.replace(re, "");
  t = t.trim();
  if (t.length < 12) return texto;                     // over-stripped — keep original
  return t.charAt(0).toUpperCase() + t.slice(1);
}

function fechaLarga(iso) {
  if (!iso) return "sin fecha";
  const [y, m, d] = iso.split("-").map(Number);
  return `${d} de ${MESES[m - 1]} de ${y}`;
}

function esc(s) {
  return s.replace(/[&<>"]/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

/* Match tokens as words, not raw substrings — so a short stopword like "la"
   stops matching inside "las" / "plana". Rule: a token of ≤3 chars must be a
   whole word (\bla\b); a longer token matches a word-prefix (\bestancia[a-z]*)
   so plurals and inflections still hit ("licencia" → "licencias"). Folded text
   is accent-stripped lowercase ASCII, so \b behaves. */
function buildMatchers(qFolded) {
  return qFolded.split(/\s+/).filter(Boolean).map((term) => {
    const e = term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const src = term.length <= 3 ? `\\b${e}\\b` : `\\b${e}[a-z0-9]*`;
    return { term, re: new RegExp(src, "g") };
  });
}
function docMatches(folded, ms) {
  return ms.every((m) => { m.re.lastIndex = 0; return m.re.test(folded); });
}
function matchRanges(folded, ms) {
  const ranges = [];
  for (const m of ms) {
    m.re.lastIndex = 0;
    let x;
    while ((x = m.re.exec(folded)) !== null) {
      ranges.push([x.index, x.index + x[0].length]);
      if (x[0].length === 0) m.re.lastIndex++;   // guard zero-width
    }
  }
  return ranges;
}

/* Highlight the matched words inside original text (indices come from the
   folded copy, which preserves positions 1:1). */
function highlight(texto, ms) {
  const spans = matchRanges(fold(texto), ms);
  if (!spans.length) return esc(texto);
  spans.sort((a, b) => a[0] - b[0]);
  const merged = [spans[0]];
  for (const [s, e] of spans.slice(1)) {
    const last = merged[merged.length - 1];
    if (s <= last[1]) last[1] = Math.max(last[1], e);
    else merged.push([s, e]);
  }
  let out = "", pos = 0;
  for (const [s, e] of merged) {
    out += esc(texto.slice(pos, s)) + "<mark>" + esc(texto.slice(s, e)) + "</mark>";
    pos = e;
  }
  return out + esc(texto.slice(pos));
}

function pasaFiltros(acta) {
  if (state.periodo && acta.periodo !== state.periodo) return false;
  if (state.desde && (!acta.fecha || acta.fecha < state.desde)) return false;
  if (state.hasta && (!acta.fecha || acta.fecha > state.hasta)) return false;
  return true;
}

function buscar(ms) {
  const hits = [];
  for (const acta of state.actas) {
    if (!pasaFiltros(acta)) continue;
    for (const item of acta.agenda_items) {
      if (docMatches(item._folded, ms)) {
        hits.push({ acta, item });
        if (hits.length >= 400) return hits;
      }
    }
  }
  return hits;
}

function renderResults() {
  const ms = buildMatchers(fold(state.q.trim()));
  const resultsEl = $("#results"), timelineEl = $("#timeline");
  if (!ms.length) {
    resultsEl.hidden = true;
    timelineEl.hidden = false;
    $("#fulltext").hidden = true;
    renderTimeline();
    return;
  }
  const hits = buscar(ms);
  resultsEl.hidden = false;
  timelineEl.hidden = true;
  $("#result-count").textContent = hits.length >= 400
    ? "400+ puntos coinciden — afina la búsqueda"
    : `${hits.length} ${hits.length === 1 ? "punto coincide" : "puntos coinciden"}`;

  if (!hits.length) {
    const filtrando = state.periodo || state.desde || state.hasta;
    $("#result-list").innerHTML = `
      <li class="result sin-resultados">
        <p class="texto">Ningún punto del órden del día contiene esos términos${
          filtrando ? " dentro del período filtrado" : ""}.</p>
        <p class="texto nota">Esta búsqueda cubre el órden del día de cada sesión. El
        contenido íntegro de las actas se está incorporando poco a poco (los PDF son
        escaneos que hay que pasar por OCR). Prueba también la búsqueda en el texto
        completo, abajo.${filtrando ? " O amplía el período." : ""}</p>
      </li>`;
    renderFulltext(ms);
    return;
  }
  $("#result-list").innerHTML = hits.slice(0, 400).map(({ acta, item }) => {
    const r = resumenDe(acta.id, item.n);
    return `
    <li class="result">
      <p class="meta mono">
        <span class="fecha">${fechaLarga(acta.fecha)}</span>
        <span>Acta ${acta.no_acta ?? "s/n"}</span>
        ${item.numeral ? `<span>Punto ${item.numeral}</span>` : ""}
        <span>${esc(acta.periodo ?? "")}</span>
      </p>
      <p class="texto">${highlight(item.texto, ms)}</p>
      ${r ? `<p class="resumen">${esc(r.resumen)} ${sentidoHTML(r.sentido)}</p>` : ""}
      ${state.summaries[acta.id] ? actaDetalleHTML(acta.id, "Ver resumen de la sesión y texto completo (OCR) →") : ""}
      ${acta.pdf_url ? `<a class="acta-link" href="${esc(acta.pdf_url)}" rel="external">Ver acta original (PDF) →</a>` : ""}
    </li>`;
  }).join("");
  renderFulltext(ms);
}

/* Full-content search over OCR text. Loaded lazily — the payload is large and
   only grows as more actas are processed, so it isn't part of the initial page.
   Honest about coverage: only the OCR'd actas are searchable here. */
async function ensureFulltext() {
  if (state.fulltext) return state.fulltext;
  const r = await fetch("fulltext.json");
  state.fulltext = (await r.json()).textos || {};
  return state.fulltext;
}
function ftFolded(id) {
  return state._ftFolded[id] ?? (state._ftFolded[id] = fold(state.fulltext[id]));
}
/* Occurrences of the query in one acta's OCR text, as context snippets.
   Requires every token present (as a word); anchors snippets on the most
   distinctive token — the longest — so "la estancia" centres on "estancia",
   not on every "la". Snippets highlight all matched words. */
function fullTextMatches(id, ms) {
  const folded = ftFolded(id);
  if (!docMatches(folded, ms)) return null;
  const anchor = ms.reduce((a, b) => (b.term.length > a.term.length ? b : a));
  const texto = state.fulltext[id];
  const positions = [];
  anchor.re.lastIndex = 0;
  let x;
  while ((x = anchor.re.exec(folded)) !== null) {
    positions.push([x.index, x.index + x[0].length]);
    if (x[0].length === 0) anchor.re.lastIndex++;
    if (positions.length >= 200) break;
  }
  const snippets = [];
  let lastEnd = -1;
  for (const [p, pe] of positions) {
    if (snippets.length >= 8) break;
    if (p < lastEnd) continue;               // already inside the previous window
    const start = Math.max(0, p - 70);
    const end = Math.min(texto.length, pe + 120);
    lastEnd = end;
    const snip = texto.slice(start, end).replace(/\s+/g, " ").trim();
    snippets.push((start > 0 ? "…" : "") + snip + (end < texto.length ? "…" : ""));
  }
  return { count: positions.length, shown: snippets.length, snippets };
}

/* Full-text search runs automatically once the OCR payload is loaded. It loads
   on the first search (not on page load, to keep the initial page light), then
   stays live for subsequent queries. */
async function loadFulltextThenRerender() {
  if (state.fulltext || state.fulltextLoading) return;
  state.fulltextLoading = true;
  try { await ensureFulltext(); }
  catch {
    state.fulltextLoading = false;
    $("#fulltext").innerHTML = `<p class="ft-intro mono">No se pudo cargar el texto completo.</p>`;
    return;
  }
  state.fulltextLoading = false;
  const ms = buildMatchers(fold(state.q.trim()));
  if (ms.length) renderFulltext(ms);
}

function renderFulltext(ms) {
  const el = $("#fulltext");
  el.hidden = false;
  const q = esc(state.q.trim());
  if (!state.fulltext) {
    el.innerHTML = `<p class="ft-intro mono">Buscando «${q}» en el texto completo de las actas escaneadas…</p>`;
    loadFulltextThenRerender();
    return;
  }
  const results = [];
  let totalOcc = 0;
  for (const acta of state.actas) {
    if (!state.fulltext[acta.id]) continue;
    const m = fullTextMatches(acta.id, ms);
    if (!m) continue;
    totalOcc += m.count;
    results.push({ acta, ...m });
  }
  const totalActas = Object.keys(state.fulltext).length;
  el.innerHTML = `
    <p class="ft-intro mono">Texto completo · «${q}» — ${totalOcc} ${totalOcc === 1 ? "coincidencia" : "coincidencias"} en ${results.length} de ${totalActas} ${totalActas === 1 ? "acta procesada" : "actas procesadas"}. El OCR abarca ${totalActas} de 74 actas del término 2024-2027; el resto se irá incorporando.</p>
    <ol class="result-list">${results.map((r) => `
      <li class="result ft-result">
        <p class="meta mono"><span class="fecha">${fechaLarga(r.acta.fecha)}</span><span>Acta ${r.acta.no_acta ?? "s/n"}</span><span>${r.count} ${r.count === 1 ? "coincidencia" : "coincidencias"}${r.shown < r.count ? ` · se muestran ${r.shown}` : ""}</span></p>
        ${r.snippets.map((s) => `<p class="texto ft-snip">${highlight(s, ms)}</p>`).join("")}
        ${state.summaries[r.acta.id] ? actaDetalleHTML(r.acta.id, "Ver texto completo (OCR) de esta acta →") : ""}
        ${r.acta.pdf_url ? `<a class="acta-link" href="${esc(r.acta.pdf_url)}" rel="external">Ver acta original (PDF) →</a>` : ""}
      </li>`).join("") || `<li class="result"><p class="texto nota">Ninguna de las ${totalActas} actas con texto completo contiene «${q}».</p></li>`}</ol>`;
}

function renderTimeline() {
  const porAno = new Map();
  for (const acta of state.actas) {
    if (!pasaFiltros(acta)) continue;
    const y = acta.fecha ? acta.fecha.slice(0, 4) : (acta.periodo || "").slice(0, 4) || "s/f";
    if (!porAno.has(y)) porAno.set(y, []);
    porAno.get(y).push(acta);
  }
  for (const actas of porAno.values()) {
    actas.sort((a, b) =>
      (b.fecha ?? "").localeCompare(a.fecha ?? "") || (b.no_acta ?? 0) - (a.no_acta ?? 0));
  }
  const years = [...porAno.keys()].sort().reverse();
  const filtered = state.periodo || state.desde || state.hasta;
  $("#timeline-body").innerHTML = years.map((y, idx) => {
    const actas = porAno.get(y);
    const open = filtered || idx === 0 ? " open" : "";
    return `
    <details class="year-group"${open}>
      <summary><h2>${esc(y)}</h2>
        <span class="count">${actas.length} ${actas.length === 1 ? "sesión" : "sesiones"}</span>
      </summary>
      ${actas.map(sessionHTML).join("")}
    </details>`;
  }).join("") || `<p class="section"><span class="empty">Ninguna sesión coincide con los filtros.</span></p>`;
}

/* The one-line description after "Acta N ·". When the acta has been processed,
   this is the AI session brief (a real summary of the sitting); otherwise it
   falls back to the lead subject of the first substantive agenda point. */
function tituloSesion(acta) {
  const brief = state.summaries[acta.id]?.sesion;
  if (brief) return { texto: brief, esBrief: true };
  const primera = acta.agenda_items.find((i) => SUSTANTIVO.test(i.texto))
    ?? acta.agenda_items.find((i) => !esProcedural(i.texto));
  const crudo = (primera ?? acta.agenda_items[0])?.texto;
  return { texto: crudo ? tituloCorto(crudo) : "Órden del día no publicado en el índice", esBrief: false };
}

/* Disclosure that reveals an acta's session brief + full OCR text on-site.
   Body is filled lazily on first open (see onDetalleClick). Only offered for
   processed actas. */
function actaDetalleHTML(id, label) {
  return `<details class="acta-detalle" data-id="${id}">
    <summary>${label}</summary>
    <div class="acta-detalle-body"></div>
  </details>`;
}

function sessionHTML(acta) {
  const resumido = state.summaries[acta.id];
  const t = tituloSesion(acta);
  const tituloVis = t.esBrief ? esc(t.texto)
    : `${esc(t.texto.slice(0, 110))}${t.texto.length > 110 ? "…" : ""}`;
  const items = acta.agenda_items.length
    ? acta.agenda_items.map((i) => {
        const r = resumenDe(acta.id, i.n);
        return `
        <li${esProcedural(i.texto) ? ' class="proc"' : ""}>
          <span class="num">${i.numeral ? esc(i.numeral) + "." : "·"}</span>
          <span class="texto">${esc(i.texto)}${r ? `
            <span class="resumen">${esc(r.resumen)} ${sentidoHTML(r.sentido)}</span>` : ""}</span>
        </li>`;
      }).join("")
    : `<li class="empty"><span class="num">·</span>
         <span class="texto">El índice oficial no publica el órden del día de esta sesión.</span></li>`;
  return `
  <details class="session">
    <summary>
      <span class="s-fecha">${acta.fecha ?? "sin fecha"}</span>
      <span class="s-titulo"><span class="s-acta">Acta ${acta.no_acta ?? "s/n"}</span> · ${tituloVis}</span>
      ${acta.pdf_url ? `<a class="s-pdf" href="${esc(acta.pdf_url)}" rel="external" onclick="event.stopPropagation()">PDF →</a>` : ""}
    </summary>
    <ol class="agenda">${items}</ol>
    ${resumido ? `<p class="resumen-nota">Resumen de la sesión y de cada punto generados con IA (${esc(resumido.modelo)}) sobre el texto OCR del acta escaneada; pueden contener errores — verifica siempre en el PDF original.</p>` : ""}
    ${resumido ? actaDetalleHTML(acta.id, "Texto completo del acta (OCR) →") : ""}
  </details>`;
}

/* Fill an acta-detalle disclosure the first time it opens: the session brief
   plus the full OCR text, with the current query highlighted. Wired once, via
   delegation, in main(). */
async function onDetalleClick(e) {
  const sum = e.target.closest(".acta-detalle > summary");
  if (!sum) return;
  const det = sum.parentElement;
  const body = det.querySelector(".acta-detalle-body");
  if (body.dataset.loaded) return;
  body.dataset.loaded = "1";
  body.innerHTML = `<p class="ft-intro mono">Cargando texto completo…</p>`;
  try { await ensureFulltext(); } catch {
    body.innerHTML = `<p class="ft-intro mono">No se pudo cargar el texto completo.</p>`;
    return;
  }
  const id = det.dataset.id;
  const s = state.summaries[id];
  const texto = state.fulltext[id];
  const ms = buildMatchers(fold(state.q.trim()));
  body.innerHTML = `
    ${s?.sesion ? `<p class="detalle-brief">${esc(s.sesion)}</p>` : ""}
    ${texto ? `<div class="ocr-text">${highlight(texto, ms)}</div>`
            : `<p class="ft-intro mono">El texto completo de esta acta aún no está disponible.</p>`}
    <p class="detalle-nota">Texto obtenido por OCR de un PDF escaneado; puede contener errores.${
      s ? ` Resumen generado con IA (${esc(s.modelo)}).` : ""} Verifica en el
      <a href="${esc(state.actas.find((a) => a.id === id)?.pdf_url || "#")}" rel="external">PDF original</a>.</p>`;
}

function renderStats(generado) {
  const n = state.actas.length;
  const items = state.actas.reduce((a, x) => a + x.agenda_items.length, 0);
  const fechas = state.actas.map((a) => a.fecha).filter(Boolean).sort();
  const periodos = new Set(state.actas.map((a) => a.periodo).filter(Boolean)).size;
  const stats = [
    ["Sesiones", n.toLocaleString("es-MX")],
    ["Puntos de agenda", items.toLocaleString("es-MX")],
    ["Período cubierto", `${fechas[0].slice(0, 4)}–${fechas[fechas.length - 1].slice(0, 4)}`],
    ["Administraciones", periodos],
  ];
  $("#statrow").innerHTML = stats.map(([label, value]) => `
    <div class="stat">
      <span class="stat-label">${label}</span>
      <span class="stat-value">${value}</span>
    </div>`).join("");

  if (generado) {
    $("#snapshot").textContent =
      `Última actualización de los datos: ${fechaLarga(generado.slice(0, 10))}.`;
  }
}

function initFilters() {
  const periodos = [...new Set(state.actas.map((a) => a.periodo).filter(Boolean))].sort().reverse();
  $("#f-periodo").insertAdjacentHTML("beforeend",
    periodos.map((p) => `<option value="${p}">${p}</option>`).join(""));

  const update = () => {
    state.q = $("#q").value;
    state.periodo = $("#f-periodo").value;
    state.desde = $("#f-desde").value;
    state.hasta = $("#f-hasta").value;
    renderResults();
  };
  let timer;
  $("#q").addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(update, 120); });
  for (const id of ["#f-periodo", "#f-desde", "#f-hasta"]) {
    $(id).addEventListener("change", update);
  }
  $("#f-clear").addEventListener("click", () => {
    $("#q").value = ""; $("#f-periodo").value = "";
    $("#f-desde").value = ""; $("#f-hasta").value = "";
    update();
  });
}

async function main() {
  const [data, summaries] = await Promise.all([
    fetch("actas.json").then((r) => r.json()),
    fetch("summaries.json").then((r) => r.json()).catch(() => ({ resumenes: {} })),
  ]);
  state.actas = data.actas;
  state.summaries = summaries.resumenes || {};
  for (const acta of state.actas) {
    for (const item of acta.agenda_items) item._folded = fold(item.texto);
  }
  renderStats(data.generado);
  initFilters();
  document.addEventListener("click", onDetalleClick); // fills OCR disclosures lazily
  renderTimeline();
}

main().catch((err) => {
  $("#statrow").textContent = "Error al cargar los datos. Recarga la página.";
  console.error(err);
});
