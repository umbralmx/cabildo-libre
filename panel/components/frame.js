/**
 * El encuadre obligatorio de toda gráfica.
 *
 * La validación la hace `Frame` de @umbralmx/umbral-plot: sin fuente lanza
 * (UMB-CHT-003), y `warnings()` avisa cuando el subtítulo no nombra ninguna
 * transformación (UMB-CHT-002) o cuando el título parece un tema y no un
 * hallazgo (UMB-CHT-001). Ninguna vista puede saltárselo.
 *
 * Guía 2.0.0, que reescribió el pie:
 *   - El subtítulo no son campos separados por puntos medios. Es una frase
 *     que nombra la transformación, la unidad, el alcance y el periodo. Una
 *     suma acumulada y un total anual dibujan curvas distintas con los mismos
 *     datos, y el subtítulo viejo no nombraba ninguna.
 *   - La línea de fuente tiene dos lados sobre una regla de 1px: origen y
 *     fecha de consulta a la izquierda, el sitio a la derecha.
 *   - La etiqueta del corte y la licencia salieron de esa línea y bajaron
 *     junto al CSV (UMB-DAT-002, UMB-DAT-004). Una gráfica que viaja sola ya
 *     no lleva licencia: fue el intercambio por una línea que sí se lee.
 *
 * El DOM se dibuja aquí, con las clases de `umbral.css`, en vez de usar
 * `Frame.render`: ese método trae los estilos en línea y esta hoja ya define
 * el mobiliario.
 */
// umbral-lint: ignore-file[chart-source-present] — este archivo ES el que
// dibuja la línea de fuente; el literal «Fuente:» vive en Frame.sourceLine().
import {Frame} from "@umbralmx/umbral-plot";
import {csvButton, fmt} from "./format.js";

/**
 * «Elaboración propia con datos de …» es la forma correcta cuando el cálculo
 * es nuestro y el dato crudo es de alguien más. Es el caso de todo el panel:
 * el Ayuntamiento publica actas escaneadas y aquí se les pasa OCR, se las
 * resume y se las agrega.
 */
const ORIGEN_POR_DEFECTO =
  "Elaboración propia con datos del Ayuntamiento de Colima (actas de cabildo)";

export function chartFrame({
  title,
  subtitle,
  consultado,
  source = ORIGEN_POR_DEFECTO,
  plot = null,
  data = [],
  download,
  columns,
  numericColumns = [],
  note = "",
  controls = null
}) {
  // Construir el Frame valida antes de dibujar: sin fuente, lanza.
  const frame = new Frame({title, subtitle, source, accessed: consultado});
  if (!download) throw new Error("una gráfica no se publica sin su CSV (UMB-A11Y-004)");

  const fig = document.createElement("figure");
  fig.className = "u-chart";
  fig.setAttribute("role", "figure");
  // El aria-label lleva el hallazgo, no el tipo de gráfica (UMB-A11Y-002).
  fig.setAttribute("aria-label", frame.ariaLabel());

  const h = document.createElement("h3");
  h.className = "u-chart-title";
  h.textContent = title;
  fig.append(h);

  const sub = document.createElement("p");
  sub.className = "u-chart-subtitle";
  sub.textContent = subtitle;
  fig.append(sub);

  if (controls) fig.append(controls);

  if (plot) {
    const holder = document.createElement("div");
    holder.className = "u-chart-plot";
    holder.append(plot);
    fig.append(holder);
  }

  // Dos lados sobre una regla de 1px; en pantalla angosta se apilan.
  const foot = document.createElement("figcaption");
  foot.className = "u-chart-foot";
  const src = document.createElement("p");
  src.className = "u-source";
  src.textContent = frame.sourceLine();
  const site = document.createElement("p");
  site.className = "u-source u-site";
  site.textContent = frame.siteLine();
  foot.append(src, site);
  fig.append(foot);

  // Debajo, la procedencia: el CSV con el corte y la licencia al lado.
  const proc = document.createElement("div");
  proc.className = "u-chart-proc";
  proc.append(csvButton({rows: data, columns, filename: download}));
  const tag = document.createElement("p");
  tag.className = "u-source";
  tag.textContent = `Corte ${consultado} · estructura CC BY 4.0 · código MIT`;
  proc.append(tag);
  fig.append(proc);

  if (note) {
    const p = document.createElement("p");
    p.className = "u-note";
    p.textContent = note;
    fig.append(p);
  }

  if (data.length) fig.append(dataTable(data, {columns, numericColumns}));

  // Los avisos del sistema se imprimen en consola, no en pantalla: son para
  // quien construye, no para quien lee.
  const w = frame.warnings();
  if (w.length) console.warn(`[${title.slice(0, 40)}…] ${w.join(" · ")}`);
  return fig;
}

/** Tabla adyacente (UMB-A11Y-003). Se construye al abrirla, no al dibujar. */
export function dataTable(data, {columns, numericColumns = [], open = false} = {}) {
  const cols = columns ?? Object.keys(data[0] ?? {});
  const numeric = new Set(numericColumns);

  const details = document.createElement("details");
  details.className = "u-details";
  const summary = document.createElement("summary");
  summary.textContent = `Ver los datos de esta gráfica (${fmt(data.length)} filas)`;
  details.append(summary);

  let construida = false;
  const construir = () => {
    if (construida) return;
    construida = true;
    details.append(tabla(data, cols, numeric));
  };
  details.addEventListener("toggle", () => details.open && construir());
  if (open) { details.open = true; construir(); }
  return details;
}

function tabla(data, cols, numeric) {
  const wrap = document.createElement("div");
  wrap.className = "u-table-wrap";
  const table = document.createElement("table");
  table.className = "u-table";

  const thead = document.createElement("thead");
  const htr = document.createElement("tr");
  for (const c of cols) {
    const th = document.createElement("th");
    th.scope = "col";
    th.textContent = c;
    if (numeric.has(c)) th.setAttribute("data-numeric", "");
    htr.append(th);
  }
  thead.append(htr);
  table.append(thead);

  const tbody = document.createElement("tbody");
  for (const row of data) {
    const tr = document.createElement("tr");
    for (const c of cols) {
      const td = document.createElement("td");
      const v = row[c];
      if (v === null || v === undefined || v === "") {
        // «Sin dato» no es cero ni vacío: lleva su palabra y su relleno
        // (UMB-COL-010, UMB-NUM-006).
        td.textContent = "sin dato";
        td.className = "u-cell";
        td.setAttribute("data-estado", "sin-registro");
      } else {
        td.textContent = typeof v === "number" ? fmt(v) : String(v);
      }
      if (numeric.has(c)) td.setAttribute("data-numeric", "");
      tr.append(td);
    }
    tbody.append(tr);
  }
  table.append(tbody);
  wrap.append(table);
  return wrap;
}

/** Una fila de cifras: `.u-kpi` de components.css, separadas por reglas. */
export function figureRow(items) {
  const div = document.createElement("div");
  div.className = "u-kpis";
  for (const it of items) {
    const cell = document.createElement("div");
    cell.className = "u-kpi";
    const label = document.createElement("span");
    label.className = "u-kpi__label";
    label.textContent = it.label;
    const value = document.createElement("span");
    value.className = "u-kpi__value";
    value.textContent = typeof it.value === "number" ? fmt(it.value) : it.value;
    cell.append(label, value);
    if (it.note) {
      const note = document.createElement("span");
      note.className = "u-kpi__note";
      note.textContent = it.note;
      cell.append(note);
    }
    div.append(cell);
  }
  return div;
}
