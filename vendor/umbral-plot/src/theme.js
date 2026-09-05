/**
 * The Observable Plot theme.
 *
 * Sets colour, type and chart furniture. It does NOT draw the frame — titles,
 * subtitles, source lines and CSV links stay the caller's job, because a theme
 * cannot know your finding. Use `Frame` from './frame.js'.
 *
 * Legends are off by default: Umbral labels series directly at the line end
 * (UMB-CHT-005), which is also why series colours need the `-text` variants.
 */
import { tokensFor, font, mode as MODES, ramp } from './tokens.js';

/**
 * Plot options for one mode.
 *
 * @param {'laboratorio'|'instrumento'} m
 * @param {object} [overrides] merged shallowly over the result
 */
export function theme(m = 'laboratorio', overrides = {}) {
  const t = tokensFor(m);
  return {
    style: {
      background: 'transparent',
      color: t.ink,
      fontFamily: `${font.body}, system-ui, sans-serif`,
      fontSize: '13px',
    },
    marginLeft: 52,
    marginBottom: 34,
    marginTop: 12,
    x: { grid: false, tickFormat: 'd', label: null },
    y: {
      grid: true,
      ticks: 5,
      tickFormat: '~s',            // 12k, 3.7M — UMB-CHT-007
      line: false,
      label: null,
    },
    color: { legend: false, range: t.series },
    ...overrides,
  };
}

/** Alias, for readers who expect Plot's own vocabulary. */
export const options = theme;

/** The categorical palette, in order. Throws past five (UMB-CHT-006). */
export function categorical(n, m = 'laboratorio') {
  const pal = tokensFor(m).series;
  if (n === undefined) return [...pal];
  if (n > 5) {
    throw new RangeError(
      `${n} series requested; the maximum is 5 (UMB-CHT-006). ` +
      'Use two charts, or group the tail into «otros».');
  }
  return pal.slice(0, n);
}

/** A sequential ramp: 'signal' (the default choropleth) or 'model'. */
export function sequential(anchor = 'signal', m = 'laboratorio') {
  const key = anchor === 'model' ? 'sequentialModel' : 'sequentialSignal';
  return [...ramp[m][key]];
}

/**
 * The diverging ramp, for change and above/below-expectation.
 *
 * Note: the two sequential ramps must never encode two variables in one figure —
 * they are indistinguishable under tritanopia (UMB-COL-009).
 */
export function diverging(m = 'laboratorio') {
  return [...ramp[m].diverging];
}

export { MODES as modes };
