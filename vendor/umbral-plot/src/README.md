# `umbral-plot/src/`

| | |
|---|---|
| `index.js` | The public surface |
| `tokens.js` | **Generated** from `tokens/build/tokens.json`. Do not edit. |
| `theme.js` | Observable Plot options: colour, type, gridlines, legends off |
| `frame.js` | `Frame` — title, subtitle, source line, `aria-label`, CSV link |
| `uncertainty.js` | Band, dashed future, `hoy` rule, direct series labels |

`tokens.js` is the only file here allowed to contain a hex. `tools/verify_packages.py` fails if any
other one does.

`theme.js` sets `color.legend: false` on purpose. Umbral labels series directly at the line end.

That is also why `label()` in `uncertainty.js` reaches for the `-text` variant. A label is small
text and needs 4.5:1. The line only needs 3:1.
