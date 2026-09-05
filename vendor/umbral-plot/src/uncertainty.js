/**
 * Uncertainty helpers — the brand signature (UMB-CHT-011).
 *
 * These return Observable Plot mark options rather than marks, so they compose
 * with whatever you are already drawing and do not require Plot as a dependency.
 */
import { tokensFor, uncertaintyBandOpacity } from './tokens.js';

/**
 * A projection or confidence band: the series colour at the brand opacity.
 *
 * @example
 * Plot.areaY(data, band({ x: 'date', y1: 'lo', y2: 'hi' }))
 */
export function band({ mode = 'laboratorio', color, ...opts } = {}) {
  const t = tokensFor(mode);
  return { fill: color ?? t.signal, fillOpacity: uncertaintyBandOpacity, stroke: null, ...opts };
}

/** A dashed stroke for anything past the last observed datum. */
export function dashedFuture({ mode = 'laboratorio', color, ...opts } = {}) {
  const t = tokensFor(mode);
  return { stroke: color ?? t.signal, strokeDasharray: '7 5', strokeWidth: 2, ...opts };
}

/**
 * The dashed vertical rule marking the present.
 *
 * Live registers under-report recent periods, so without this the final drop in a
 * series reads as an improvement rather than as missing data.
 */
export function today({ mode = 'laboratorio', label = 'hoy', ...opts } = {}) {
  const t = tokensFor(mode);
  return {
    rule: { stroke: t.caption, strokeDasharray: '4 3', ...opts },
    label: { text: label, fill: t.caption, fontFamily: 'monospace', fontSize: 11, dy: -6 },
  };
}

/**
 * A direct series label at the line end, instead of a legend (UMB-CHT-005).
 *
 * Uses the `-text` variant, because a label is small text and needs 4.5:1 while the
 * line itself only needs 3:1.
 */
export function label(series = 'signal', { mode = 'laboratorio', ...opts } = {}) {
  const t = tokensFor(mode);
  const key = `${series}-text` in t ? `${series}-text` : series;
  return { fill: t[key] ?? t.ink, textAnchor: 'start', dx: 6, ...opts };
}
