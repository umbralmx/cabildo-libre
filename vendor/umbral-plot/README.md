# @umbralmx/umbral-plot

The Umbral design system for [Observable Plot](https://observablehq.com/plot/).

```bash
npm install @umbralmx/umbral-plot
```

```js
import * as Plot from '@observablehq/plot';
import { theme, Frame, band, today, label } from '@umbralmx/umbral-plot';
import '@umbralmx/umbral-plot/dist/umbral.css';

// umbral-lint: ignore[chart-source-present] — the frame is the next example
const plot = Plot.plot({
  ...theme('laboratorio'),
  marks: [
    Plot.areaY(data, band({ x: 'fecha', y1: 'lo', y2: 'hi' })),
    Plot.lineY(data, { x: 'fecha', y: 'n', stroke: 'signal' }),
    Plot.text([last], label('signal', { x: 'fecha', y: 'n', text: () => 'Desapariciones' })),
  ],
});
```

## The frame is required

```js
const frame = new Frame({
  title: 'Los registros crecen 9% anual desde 2015',
  subtitle: 'México · registros por año · escenario base con IC 80%',
  source: 'RNPDNO (CNB/SEGOB)', accessed: '2026-07-09', snapshot: 'rnpdno-2026-07',
});

document.body.append(frame.render(plot, { csv: 'serie.csv' }));
```

`render()` returns a `<figure>`. It carries the title, the subtitle, an `aria-label` with the
finding (UMB-A11Y-002), the source line above a 1px rule, and the CSV link (UMB-A11Y-004).

Constructing a `Frame` without `source` throws `MissingSourceError`. `categorical(n)` throws past
five (UMB-CHT-006).

## Ramps

```js
sequential('signal')   // the default choropleth ramp
sequential('model')    // never in the same figure as the above — UMB-COL-009
diverging()            // change, surplus/deficit, above/below expectation
```

The two sequential ramps are indistinguishable under tritanopia, which is why using both in one
figure is a rule violation rather than a style preference.

## Components

Ten CSS components, in the minimal idiom. `src/components.css` is **authored**, not generated — it
is the one stylesheet in the system a human edits.

```js
import '@umbralmx/umbral-plot/dist/umbral.css';      // the tokens
import '@umbralmx/umbral-plot/components.css';        // the components
```

`.u-rule` `.u-label` `.u-rows` `.u-btn` `.u-seg` `.u-input` `.u-table` `.u-cell` `.u-dialog`
`.u-kpi` — they cover the shadcn/ui forms a data surface actually needs. The full catalogue and the
verdict on each of its 66 components is `guide/16-componentes.md`.

It writes no value: every colour, size and space is a `var(--u-*)`, so load the tokens first.
`tools/verify_packages.py` fails on a hex or a shadow appearing here.

## Where the values come from

`src/tokens.js` and `dist/umbral.css` are generated from `tokens/build/` and verified against it in
CI. Nothing else in `src/` contains a hex.
