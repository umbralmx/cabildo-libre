/* Metodología pública — Actas Abiertas, Cabildo de Colima.

   Esta página explica el método a un público no técnico (organizaciones,
   investigación, prensa, servidores públicos). Todas sus cifras salen de
   `analytics-<termino>.json` y `actas.json` en vez de estar escritas a mano,
   por una razón concreta: el panel llegó a publicar «74 sesiones» durante
   semanas después de que el término creciera a 78. Una página de metodología
   que miente sobre su propio tamaño no sirve para lo que existe.

   Si un dato no carga, el marcador se queda con el texto que trae el HTML y no
   se rompe la lectura: la página tiene que ser legible sin JavaScript.
*/

const TERMINO = '2024-2027';
const $ = (id) => document.getElementById(id);

const nf = new Intl.NumberFormat('es-MX');
const fmtN = (n) => nf.format(n);
const fmtPct = (x, d = 1) => `${(x * 100).toFixed(d)}%`;

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

/** Sustituye el contenido de un marcador sólo si hay dato. El HTML trae un
    valor de respaldo para que la página se lea con JS desactivado. */
function slot(id, valor) {
  const n = $(id);
  if (n && valor != null) n.textContent = valor;
}

function stat(label, value, det) {
  const s = el('div', 'u-kpi');
  s.append(el('span', 'u-kpi__label', label));
  s.append(el('span', 'u-kpi__value', value));
  // UMB-NUM-002 — a figure without its denominator is not a rate, so the
  // qualifier rides with the KPI rather than sitting in a footnote.
  if (det) s.append(el('span', 'u-kpi__note', det));
  return s;
}

/** Los dos medidores del arreglo de lectura. El «antes» es un hecho histórico
    fechado —no un dato vivo— y se etiqueta como tal para que nadie lo lea como
    una medición actual. El «ahora» sí viene del archivo. */
function antesDespues(cont, lec, pctSinResultado) {
  const wrap = el('div', 'medidores');
  [
    {
      lab: 'Antes — texto del acta que llegaba a leerse',
      v: 0.25,
      tono: '',
      det: '58 % de las decisiones quedaba sin resultado legible · medido en julio de 2026',
    },
    {
      lab: 'Ahora — texto del acta que llega a leerse',
      v: lec && lec.proporcion != null ? lec.proporcion : null,
      tono: 'signal',
      det: lec && lec.proporcion != null
        ? `${fmtPct(pctSinResultado)} de las decisiones queda sin resultado legible · `
          + `${fmtN(lec.actas_completas)} actas leídas completas, ${fmtN(lec.ventanas_fallidas)} lecturas fallidas`
        : 'sin medir',
    },
  ].forEach(({ lab, v, det, tono }) => {
    const m = el('div', 'medidor');
    m.append(el('div', 'medidor-lab', lab));
    const track = el('div', 'medidor-track');
    if (v != null) {
      const fill = el('div', `medidor-fill ${tono}`.trim());
      fill.style.width = `${v * 100}%`;
      track.append(fill);
    }
    m.append(track);
    m.append(el('div', 'medidor-val mono', v != null ? fmtPct(v, 0) : '—'));
    m.append(el('div', 'medidor-det', det));
    wrap.append(m);
  });
  cont.append(wrap);
}

async function main() {
  const [an, actas] = await Promise.all([
    fetch(`analytics-${TERMINO}.json`).then((r) => (r.ok ? r.json() : null)).catch(() => null),
    fetch('actas.json').then((r) => (r.ok ? r.json() : null)).catch(() => null),
  ]);
  if (!an) return;

  const cob = an.cobertura || {};
  const dec = an.decisiones || {};
  const lec = an.lectura || {};
  const sentidos = dec.por_sentido || {};
  const nPuntos = dec.n_puntos || 0;
  const sinResultado = sentidos.no_determinable || 0;
  // La base es la suma de `por_sentido`, no `n_puntos`. El agregador sólo clasifica
  // el sentido de los puntos sustantivos —un trámite no tiene resultado que leer—,
  // así que dividir entre el total de puntos mezcla dos universos y rebaja la cifra
  // (2.7 % en vez de 4.3 %). Justo la sección 06 apoya su argumento en este número.
  const baseSentido = Object.values(sentidos).reduce((a, b) => a + b, 0);
  const pctSinResultado = baseSentido ? sinResultado / baseSentido : 0;

  // ── statrow ────────────────────────────────────────────────────────────────
  const sr = $('statrow');
  if (sr) {
    sr.append(stat('Actas leídas íntegras', fmtN(cob.con_resumen || 0),
      `de ${fmtN(cob.actas_en_termino || 0)} del término ${TERMINO}`));
    sr.append(stat('Decisiones fichadas', fmtN(dec.n_sustantivos || 0),
      `sobre ${fmtN(nPuntos)} puntos del órden del día`));
    sr.append(stat('Texto del acta que se lee',
      lec.proporcion != null ? fmtPct(lec.proporcion, 0) : '—',
      `${fmtN(lec.chars_ocr || 0)} caracteres de OCR`));
    sr.append(stat('Sin resultado legible', fmtPct(pctSinResultado),
      `${fmtN(sinResultado)} de ${fmtN(baseSentido)} decisiones`));
  }

  // ── marcadores en prosa ────────────────────────────────────────────────────
  if (actas) {
    const filas = Array.isArray(actas) ? actas : actas.actas || [];
    if (filas.length) slot('n-sesiones-corpus', fmtN(filas.length));
  }
  slot('n-actas-b', fmtN(cob.actas_en_termino || 0));
  slot('n-actas-c', fmtN(cob.actas_en_termino || 0));
  slot('n-actas-d', fmtN(cob.actas_en_termino || 0));

  const est = an.estructura || {};
  if (est.orden_del_dia_modificado != null) {
    slot('n-modificadas', fmtN(est.orden_del_dia_modificado));
  }
  if (est.actas_que_se_contradicen != null) {
    slot('n-contradictorias', fmtN(est.actas_que_se_contradicen));
  }
  if (lec.chars_ocr) {
    slot('n-caracteres', `${fmtN(Math.round(lec.chars_ocr / 1e6))} millones`);
  }

  const cont = $('c-antes-despues');
  if (cont) antesDespues(cont, lec, pctSinResultado);

  if (an.generado) {
    const f = new Date(an.generado);
    slot('snapshot', `Cifras de esta página: corte del ${f.toLocaleDateString('es-MX',
      { day: 'numeric', month: 'long', year: 'numeric' })}. Se recalculan en cada procesamiento.`);
    // UMB-CHT-003 — the access date belongs in each source line, in ISO
    // (UMB-NUM-003), and is read from the payload so it cannot go stale.
    const iso = an.generado.slice(0, 10);
    document.querySelectorAll('.fig-src .consulta').forEach((n) => {
      n.textContent = ` Consulta realizada el ${iso}.`;
    });
  }
}

main();
