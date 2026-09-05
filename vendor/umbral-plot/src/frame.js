/**
 * The chart frame: finding-title, subtitle, source line.
 *
 * `Frame` throws without a source. The v1.0 engineering doc asked for exactly this
 * ("a chart with no source should throw in dev") and nobody built it; the Phase 0
 * audit then found charts shipping without one. A chart circulates without its page
 * the moment someone screenshots it, so the source line is the only context that
 * travels with it.
 */
import { tokensFor, font } from './tokens.js';

const ACCESSED = /\d{4}-\d{2}-\d{2}/;

export class MissingSourceError extends Error {
  constructor(message) {
    super(message);
    this.name = 'MissingSourceError';
    this.rule = 'UMB-CHT-003';
  }
}

export class Frame {
  /**
   * @param {object} o
   * @param {string} o.title     states the finding, as a sentence
   * @param {string} o.subtitle  how the figure is built: transformation, unit,
   *                             scope, period (UMB-CHT-002)
   * @param {string} o.source    required — the origin, as a phrase
   * @param {string} [o.accessed]  YYYY-MM-DD, ISO (UMB-NUM-003)
   * @param {string} [o.site]      shown on the right of the source line
   */
  constructor({
    title, subtitle, source, accessed = '',
    site = 'umbral.org.mx', strict = true,
  } = {}) {
    if (!source || !String(source).trim()) {
      throw new MissingSourceError(
        'a chart needs its source (UMB-CHT-003). Pass source, and accessed — a live '
        + 'register\'s counts change between queries, so a chart with no access date '
        + 'cannot be reconciled later. The snapshot tag and the licence belong on the '
        + 'page (UMB-DAT-002, UMB-DAT-004), not on this line.');
    }
    if (!title || !String(title).trim()) {
      throw new Error('a chart title states the finding as a sentence (UMB-CHT-001)');
    }
    if (strict && (!subtitle || !String(subtitle).trim())) {
      throw new Error(
        'a chart subtitle says how the figure is built — the transformation, the unit, '
        + 'the scope and the period (UMB-CHT-002). For example: '
        + '«Suma acumulada de personas desaparecidas por estado, 2021-2026». '
        + 'Pass strict: false only for a deliberately bare figure.');
    }
    Object.assign(this, { title, subtitle, source, accessed, site });
  }

  /**
   * The left half of the source line: where the data came from, and when it was
   * read. The licence and the snapshot tag are deliberately absent — they live on
   * the page (UMB-DAT-004, UMB-DAT-002). A five-field line does not survive a
   * social card or a slide, which is what 2.0 fixed.
   */
  // umbral-lint: ignore[snapshot-tag] — the template below is built, not quoted
  sourceLine() {
    const origin = String(this.source).trim().replace(/\.$/, '');
    const line = `Fuente: ${origin}.`;
    return this.accessed ? `${line} Consulta realizada el ${this.accessed}.` : line;
  }

  /** The right half: the attribution, read at a glance. */
  siteLine() {
    return String(this.site).trim();
  }

  /** The aria-label carries the finding, not the chart type (UMB-A11Y-002). */
  ariaLabel() {
    return String(this.title).trim();
  }

  /** Non-fatal gaps worth surfacing in review. */
  warnings() {
    const out = [];
    if (!ACCESSED.test(this.accessed)) {
      out.push('no ISO access date; pass accessed: "2026-07-20" (UMB-CHT-003)');
    }
    if (!/acumulad|total|tasa|promedio|mediana|cambio|porcentaje|suma|\d{4}/i.test(this.subtitle ?? '')) {
      out.push('the subtitle names no transformation and no period (UMB-CHT-002)');
    }
    if (String(this.title).trimEnd().endsWith('.')) out.push('chart titles carry no full stop');
    if (String(this.title).split(/\s+/).length < 4) {
      out.push('the title looks like a topic, not a finding (UMB-CHT-001)');
    }
    return out;
  }

  /**
   * Wrap a rendered plot in its frame.
   *
   * @param {Element} plot        the node Plot.plot() returned
   * @param {object}  [o]
   * @param {string}  [o.mode]
   * @param {string}  [o.csv]     href for the downloadable CSV (UMB-A11Y-004)
   * @param {Element} [o.table]   an adjacent data table (UMB-A11Y-003)
   * @returns {Element} a <figure>
   */
  render(plot, { mode = 'laboratorio', csv = null, table = null, document: doc } = {}) {
    const d = doc ?? globalThis.document;
    if (!d) throw new Error('Frame.render needs a DOM; pass { document }');
    const t = tokensFor(mode);

    const fig = d.createElement('figure');
    fig.setAttribute('role', 'figure');
    fig.setAttribute('aria-label', this.ariaLabel());
    fig.style.cssText = 'margin:0;display:flex;flex-direction:column;gap:4px';

    const h = d.createElement('h3');
    h.textContent = this.title;
    h.style.cssText = `margin:0;font-family:'${font.display}',system-ui,sans-serif;`
      + `font-weight:500;letter-spacing:-0.02em;font-size:22px;color:${t.ink}`;
    fig.append(h);

    if (this.subtitle) {
      const p = d.createElement('p');
      p.textContent = this.subtitle;
      p.style.cssText = `margin:0 0 8px;font-family:'${font.body}',system-ui,sans-serif;`
        + `font-size:14px;color:${t.muted}`;
      fig.append(p);
    }

    if (plot) fig.append(plot);
    if (table) fig.append(table);

    // The caption is two-sided above one 1px rule: origin and access date on the
    // left, the site on the right (UMB-CHT-003). It wraps to stacked on a narrow
    // viewport rather than letting the two halves collide.
    const cap = d.createElement('figcaption');
    cap.style.cssText = `margin-top:8px;padding-top:8px;border-top:1px solid ${t.border};`
      + `font-family:'${font.mono}',ui-monospace,monospace;font-size:12px;color:${t.caption};`
      + 'display:flex;flex-wrap:wrap;gap:8px 16px;justify-content:space-between;'
      + 'align-items:baseline';

    const left = d.createElement('span');
    left.textContent = this.sourceLine();
    if (csv) {
      const a = d.createElement('a');
      a.href = csv;
      a.setAttribute('download', '');
      a.textContent = 'Descargar CSV';
      a.style.cssText = `margin-left:12px;color:${t['signal-text']}`;
      left.append(a);
    }

    const right = d.createElement('span');
    right.textContent = this.siteLine();

    cap.append(left, right);
    fig.append(cap);
    return fig;
  }
}

export const frame = (o) => new Frame(o);
