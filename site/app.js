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

const state = { actas: [], q: "", periodo: "", desde: "", hasta: "" };

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

/* Highlight every folded occurrence of each term inside original text. */
function highlight(texto, terms) {
  const folded = fold(texto);
  const spans = [];
  for (const t of terms) {
    let i = 0;
    while ((i = folded.indexOf(t, i)) !== -1) {
      spans.push([i, i + t.length]);
      i += t.length;
    }
  }
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

function buscar(terms) {
  const hits = [];
  for (const acta of state.actas) {
    if (!pasaFiltros(acta)) continue;
    for (const item of acta.agenda_items) {
      if (terms.every((t) => item._folded.includes(t))) {
        hits.push({ acta, item });
        if (hits.length >= 400) return hits;
      }
    }
  }
  return hits;
}

function renderResults() {
  const terms = fold(state.q.trim()).split(/\s+/).filter(Boolean);
  const resultsEl = $("#results"), timelineEl = $("#timeline");
  if (!terms.length) {
    resultsEl.hidden = true;
    timelineEl.hidden = false;
    renderTimeline();
    return;
  }
  const hits = buscar(terms);
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
        <p class="texto nota">La búsqueda cubre el órden del día de cada sesión, no el
        contenido íntegro de las actas: los PDF son escaneos sin capa de texto. Un asunto
        puede haberse discutido sin que su nombre aparezca en el órden del día.${
          filtrando ? " Prueba ampliando el período." : ""}</p>
      </li>`;
    return;
  }
  $("#result-list").innerHTML = hits.slice(0, 400).map(({ acta, item }) => `
    <li class="result">
      <p class="meta mono">
        <span class="fecha">${fechaLarga(acta.fecha)}</span>
        <span>Acta ${acta.no_acta ?? "s/n"}</span>
        ${item.numeral ? `<span>Punto ${item.numeral}</span>` : ""}
        <span>${esc(acta.periodo ?? "")}</span>
      </p>
      <p class="texto">${highlight(item.texto, terms)}</p>
      ${acta.pdf_url ? `<a class="acta-link" href="${esc(acta.pdf_url)}" rel="external">Ver acta original (PDF) →</a>` : ""}
    </li>`).join("");
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

function sessionHTML(acta) {
  const primera = acta.agenda_items.find((i) => SUSTANTIVO.test(i.texto))
    ?? acta.agenda_items.find((i) => !esProcedural(i.texto));
  const crudo = (primera ?? acta.agenda_items[0])?.texto;
  const titulo = crudo ? tituloCorto(crudo) : "Órden del día no publicado en el índice";
  const items = acta.agenda_items.length
    ? acta.agenda_items.map((i) => `
        <li${esProcedural(i.texto) ? ' class="proc"' : ""}>
          <span class="num">${i.numeral ? esc(i.numeral) + "." : "·"}</span>
          <span class="texto">${esc(i.texto)}</span>
        </li>`).join("")
    : `<li class="empty"><span class="num">·</span>
         <span class="texto">El índice oficial no publica el órden del día de esta sesión.</span></li>`;
  return `
  <details class="session">
    <summary>
      <span class="s-fecha">${acta.fecha ?? "sin fecha"}</span>
      <span class="s-titulo"><span class="s-acta">Acta ${acta.no_acta ?? "s/n"}</span> · ${esc(titulo.slice(0, 110))}${titulo.length > 110 ? "…" : ""}</span>
      ${acta.pdf_url ? `<a class="s-pdf" href="${esc(acta.pdf_url)}" rel="external" onclick="event.stopPropagation()">PDF →</a>` : ""}
    </summary>
    <ol class="agenda">${items}</ol>
  </details>`;
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
  const resp = await fetch("actas.json");
  const data = await resp.json();
  state.actas = data.actas;
  for (const acta of state.actas) {
    for (const item of acta.agenda_items) item._folded = fold(item.texto);
  }
  renderStats(data.generado);
  initFilters();
  renderTimeline();
}

main().catch((err) => {
  $("#statrow").textContent = "Error al cargar los datos. Recarga la página.";
  console.error(err);
});
