/**
 * Las gráficas del panel.
 *
 * Una decisión gobierna todas: **ninguna codifica nada por color.**
 *
 * El gris `muted` y `signal` de Umbral no se separan como par categórico
 * bajo deuteranopía (ΔE 1.8, medido con el validador de dataviz), así que
 * cada gráfica es de una sola serie: la identidad viene de la etiqueta de
 * la fila y de la cifra en mono, nunca del tono (UMB-A11Y-005). El
 * presupuesto de `signal` de toda la página se gasta en un solo elemento
 * —el medidor de profundidad de lectura— porque esa es la cifra de la que
 * depende leer todo lo demás (UMB-COL-004).
 */
// umbral-lint: ignore-file[chart-source-present] — este archivo dibuja las
// marcas, no publica gráficas. La línea de fuente la pone components/frame.js,
// y `chartFrame` se NIEGA a construir sin ella: `Frame` lanza MissingSourceError
// (UMB-CHT-003). La garantía es más fuerte que la heurística, que mira un
// archivo a la vez y no puede ver el encuadre desde aquí. El propio lint.py lo
// dice en su encabezado.
import * as Plot from "npm:@observablehq/plot";
import {theme} from "@umbralmx/umbral-plot";
import {MODE, T, fmt, fmtMXNCorto} from "./format.js";

// El tema del sistema, resuelto al modo del tablero.
const base = theme(MODE);

/** Barras horizontales, ordenadas por valor. La forma de un ranking. */
export function barrasH(rows, {x, y, ancho = 1080, alto = null, formatoX = fmt, color = null} = {}) {
  return Plot.plot({
    ...base,
    width: ancho,
    height: alto ?? Math.max(140, rows.length * 34 + 46),
    marginLeft: 210,
    marginRight: 76,
    x: {
      // El eje de una barra empieza en cero, sin excepción (UMB-CHT-008).
      domain: [0, Math.max(...rows.map((r) => r[x])) * 1.08 || 1],
      grid: true,
      label: null,
      tickFormat: formatoX
    },
    y: {label: null, domain: rows.map((r) => r[y])},
    marks: [
      Plot.barX(rows, {x, y, fill: color ?? T.ink, sort: null}),
      // La cifra al final de la barra: se lee sin cruzar a una leyenda
      // (UMB-CHT-005 — etiquetado directo, nunca caja de leyenda).
      Plot.text(rows, {
        x, y, text: (d) => formatoX(d[x]),
        textAnchor: "start", dx: 6, fill: T.ink,
        fontFamily: "IBM Plex Mono, ui-monospace, monospace"
      }),
      Plot.ruleX([0], {stroke: T.baseline})
    ]
  });
}

/** Columnas en el tiempo. Sólo retícula horizontal (UMB-CHT-004). */
export function columnas(rows, {x, y, ancho = 1080, formatoX = (d) => d} = {}) {
  return Plot.plot({
    ...base,
    width: ancho,
    height: 260,
    marginLeft: 52,
    marginBottom: 46,
    x: {label: null, tickFormat: formatoX, tickRotate: -45},
    y: {domain: [0, Math.max(...rows.map((r) => r[y])) * 1.12 || 1], grid: true, label: null},
    marks: [
      Plot.barY(rows, {x, y, fill: T.ink}),
      Plot.ruleY([0], {stroke: T.baseline})
    ]
  });
}

/**
 * El medidor de profundidad de lectura — el único elemento en `signal` de
 * toda la página. El resto del fondo dibuja el 100 % para que la parte no
 * leída se vea como hueco y no como ausencia (UMB-COL-010).
 */
export function medidor(rows, {ancho = 1080} = {}) {
  return Plot.plot({
    ...base,
    width: ancho,
    height: rows.length * 62 + 40,
    marginLeft: 210,
    marginRight: 76,
    x: {domain: [0, 1], grid: true, label: null, tickFormat: (d) => `${Math.round(d * 100)}%`},
    y: {label: null, domain: rows.map((r) => r.etiqueta)},
    marks: [
      // El riel entero: lo que falta se ve, no se omite.
      Plot.barX(rows, {x: 1, y: "etiqueta", fill: T.gridline, sort: null}),
      Plot.barX(rows, {x: "valor", y: "etiqueta", fill: (d) => (d.signal ? T.signal : T.ink), sort: null}),
      Plot.text(rows, {
        x: "valor", y: "etiqueta", text: (d) => `${(d.valor * 100).toFixed(1)}%`,
        textAnchor: "start", dx: 6, fill: T.ink,
        fontFamily: "IBM Plex Mono, ui-monospace, monospace"
      }),
      Plot.ruleX([0], {stroke: T.baseline})
    ]
  });
}

export {fmtMXNCorto};
