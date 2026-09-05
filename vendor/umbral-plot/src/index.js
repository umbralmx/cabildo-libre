/**
 * umbral-plot — the Umbral design system for Observable Plot.
 *
 *   import { theme, Frame, band, today, label } from '@umbralmx/umbral-plot';
 *   import '@umbralmx/umbral-plot/dist/umbral.css';
 *
 * Token values come from `src/tokens.js`, generated from `tokens/build/tokens.json`
 * at build time and verified byte-identical in CI. Nothing here writes a hex.
 */
export * as tokens from './tokens.js';
export { theme, options, sequential, diverging, categorical } from './theme.js';
export { Frame, MissingSourceError, frame } from './frame.js';
export { band, today, dashedFuture, label } from './uncertainty.js';
export { version } from './tokens.js';
