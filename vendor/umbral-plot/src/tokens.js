/**
 * tokens.js — GENERATED from tokens/build/tokens.json at v2.0.0. Do not edit.
 *
 * umbralmx/umbral-style-guide · code MIT · content CC BY 4.0
 */

export const version = "2.0.0";

export const font = {
  "display": "Space Grotesk",
  "body": "IBM Plex Sans",
  "mono": "IBM Plex Mono",
  "displayWeight": 500,
  "displayTracking": "-0.02em"
};

export const scale = {
  "unit": 8,
  "radius": 0,
  "radiusMax": 2,
  "rule": 1,
  "measure": "65ch"
};

export const uncertaintyBandOpacity = 0.15;

/** Semantic tokens, per mode. Read these; never retype a hex. */
export const mode = {
  "laboratorio": {
    "base": "#f2f3f1",
    "panel": "#fafaf8",
    "ink": "#16191c",
    "muted": "#565d57",
    "caption": "#6c706d",
    "border": "#dde0dc",
    "gridline": "#e6e8e4",
    "baseline": "#c4c9c4",
    "signal": "#128273",
    "signal-text": "#227c6f",
    "model": "#5a63d8",
    "model-text": "#5962d7",
    "alert": "#c8503f",
    "alert-text": "#be4737",
    "series-4": "#902a00",
    "series-5": "#6331a0",
    "missing": "#e3e5e1",
    "series": [
      "#128273",
      "#5a63d8",
      "#565d57",
      "#c8503f",
      "#902a00",
      "#6331a0"
    ]
  },
  "instrumento": {
    "base": "#101418",
    "panel": "#171c22",
    "ink": "#edf1f4",
    "muted": "#8b95a0",
    "caption": "#7a848f",
    "border": "#2a3138",
    "gridline": "#232a31",
    "baseline": "#3a434c",
    "signal": "#5fd4c4",
    "signal-text": "#5fd4c4",
    "model": "#8b93f8",
    "model-text": "#8b93f8",
    "alert": "#e26a5a",
    "alert-text": "#e26a5a",
    "series-4": "#ffce2c",
    "series-5": "#b454b3",
    "missing": "#1d242b",
    "series": [
      "#5fd4c4",
      "#8b93f8",
      "#8b95a0",
      "#e26a5a",
      "#ffce2c",
      "#b454b3"
    ]
  }
};

/** Sequential and diverging ramps, per mode. */
export const ramp = {
  "laboratorio": {
    "sequentialSignal": [
      "#eaf5f2",
      "#c1d9d4",
      "#98bfb6",
      "#6fa59a",
      "#448b7e",
      "#007264",
      "#00544a"
    ],
    "sequentialModel": [
      "#eff1fc",
      "#cbd2ef",
      "#a8b2e2",
      "#8793d4",
      "#6874c5",
      "#4c54b6",
      "#3431a5"
    ],
    "diverging": [
      "#942316",
      "#b05b4d",
      "#ca8c81",
      "#e0bdb6",
      "#f4efee",
      "#b2cdc7",
      "#79a99f",
      "#3c8679",
      "#006155"
    ]
  },
  "instrumento": {
    "sequentialSignal": [
      "#152220",
      "#233f3a",
      "#325f57",
      "#428075",
      "#51a395",
      "#62c7b6",
      "#72edd8"
    ],
    "sequentialModel": [
      "#1c1f29",
      "#33374f",
      "#4a5178",
      "#646da3",
      "#7e8ad1",
      "#9aa9ff",
      "#c4ceff"
    ],
    "diverging": [
      "#bc4b3a",
      "#984538",
      "#753e34",
      "#543530",
      "#332c2b",
      "#39554f",
      "#477d73",
      "#54a899",
      "#60d5c1"
    ]
  }
};

export const modes = ['laboratorio', 'instrumento'];

/** Tokens for one mode. Throws rather than silently returning undefined. */
export function tokensFor(m = 'laboratorio') {
  if (!modes.includes(m)) {
    throw new Error(`unknown Umbral mode "${m}" — expected one of ${modes.join(', ')}`);
  }
  return mode[m];
}

export default { version, font, scale, mode, ramp, modes, tokensFor, uncertaintyBandOpacity };
