/* Panel por administración (Fase 3 · L4) — Actas Abiertas, Cabildo de Colima.
   Reads site/analytics-<termino>.json and renders the indicators that the data
   actually supports today (docs/indicadores-revision.md): T1+N1 cobertura,
   I3 cadencia, D2 mezcla de asuntos, M4 dinero declarado, P1 asistencia (+P5
   suplencias), G1/N2 colonias, T3 integridad.

   Three rules this file exists to enforce:

   1. **Every figure states its base.** A chart computed over 25 of 74 actas says
      so, inline, next to the chart — never in a footnote nobody reads. Titles are
      generated from the data so they cannot go stale as coverage grows.
   2. **No colour carries meaning.** Umbral's gray and signal fail CVD separation
      as a categorical pair (ΔE 1.8 deutan — verified with the dataviz validator),
      so every chart here is single-series: identity comes from the row label and
      the value label, never from hue. `signal` is spent on exactly one element in
      the whole page — the reading-depth meter — which is the number the rest of
      the panel depends on.
   3. **A gap is drawn as a gap.** Missing outcomes, unread text and unmatched
      names are rendered, not omitted or zero-filled.
*/

const TERMINO = '2024-2027';
const $ = (id) => document.getElementById(id);

// ── formatting ───────────────────────────────────────────────────────────────
const nf = new Intl.NumberFormat('es-MX');
const fmtN = (n) => nf.format(n);
const fmtPct = (x, d = 0) => `${(x * 100).toFixed(d)}%`;
const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

function fmtMXN(v) {
  if (v == null) return 'sin cifra';
  return '$' + nf.format(Math.round(v));
}
/** Abbreviated pesos for tight labels. Everything from a million up is expressed
    in millions — never "MM", which reads as *millones* to some and as *mil
    millones* to others, exactly the ambiguity a money figure cannot afford. */
function fmtMXNCorto(v) {
  if (v == null) return '—';
  const a = Math.abs(v);
  if (a >= 1e6) return `$${nf.format(Math.round(v / 1e6))}M`;
  if (a >= 1e3) return `$${Math.round(v / 1e3)}k`;
  return '$' + nf.format(v);
}
function fmtFecha(iso) {
  if (!iso) return 'sin fecha';
  const [y, m, d] = iso.split('-');
  return `${Number(d)} ${MESES[Number(m) - 1]} ${y}`;
}
const CATEGORIA_ES = {
  obra_publica: 'Obra pública', licencia: 'Licencias y permisos',
  fraccionamiento: 'Fraccionamientos', presupuesto_finanzas: 'Presupuesto y finanzas',
  nombramiento: 'Nombramientos', convenio: 'Convenios',
  reglamento_normativo: 'Reglamentos', patrimonio: 'Patrimonio',
  tramite: 'Trámite interno', otro: 'Otro',
};
const SENTIDO_ES = {
  aprobado: 'Aprobado', rechazado: 'Rechazado', aplazado: 'Aplazado',
  retirado: 'Retirado', no_determinable: 'Sin resultado legible',
};

// ── DOM helpers ──────────────────────────────────────────────────────────────
function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

/** A chart block: title states the finding, subtitle gives base/unit, source line
    in mono above a 1px rule (brand §6.1). */
function figura(parent, { titulo, subtitulo, fuente }) {
  const fig = el('figure', 'fig');
  const cap = el('figcaption');
  cap.append(el('h3', 'fig-title', titulo));
  if (subtitulo) cap.append(el('p', 'fig-sub', subtitulo));
  fig.append(cap);
  const body = el('div', 'fig-body');
  fig.append(body);
  if (fuente) fig.append(el('p', 'fig-src mono', fuente));
  parent.append(fig);
  return body;
}

/** The accessible twin of every chart: the same numbers as a real table
    (dataviz §6 — identity is never colour-alone, a table view always exists). */
function tablaDatos(parent, cols, rows, resumen = 'Ver los datos') {
  const d = el('details', 'datos');
  d.append(el('summary', null, resumen));
  const t = el('table', 'tabla');
  const thead = el('thead');
  const htr = el('tr');
  cols.forEach((c) => {
    const th = el('th', null, c.label);
    if (c.num) th.className = 'num';
    htr.append(th);
  });
  thead.append(htr);
  t.append(thead);
  const tb = el('tbody');
  rows.forEach((r) => {
    const tr = el('tr');
    cols.forEach((c) => {
      const td = el('td', c.num ? 'num mono' : null);
      const nodo = c.get(r);
      td.append(nodo instanceof Node ? nodo : document.createTextNode(nodo));
      tr.append(td);
    });
    tb.append(tr);
  });
  t.append(tb);
  d.append(t);
  parent.append(d);
}

/** Horizontal bars. Single series by design: no hue encodes anything, the label
    and the mono value carry identity. Rounded data-end, 2px surface gaps. */
function barrasH(parent, rows, { unidad = '', total = null } = {}) {
  const max = Math.max(...rows.map((r) => r.valor), 0) || 1;
  const wrap = el('div', 'barras');
  rows.forEach((r) => {
    const row = el('div', 'barra-row');
    const lab = el('div', 'barra-lab', r.etiqueta);
    if (r.titulo) lab.title = r.titulo;
    const track = el('div', 'barra-track');
    const fill = el('div', 'barra-fill');
    fill.style.width = `${(r.valor / max) * 100}%`;
    const pct = total ? ` · ${fmtPct(r.valor / total)}` : '';
    track.title = `${r.etiqueta}: ${r.texto ?? fmtN(r.valor)}${unidad}${pct}`;
    track.append(fill);
    const val = el('div', 'barra-val mono', r.texto ?? fmtN(r.valor));
    row.append(lab, track, val);
    wrap.append(row);
  });
  parent.append(wrap);
}

/** Columns over time. Horizontal gridlines only, no vertical rules, no fills. */
function columnas(parent, rows, { etiquetaY = '' } = {}) {
  const max = Math.max(...rows.map((r) => r.valor), 0) || 1;
  const wrap = el('div', 'cols');
  const grid = el('div', 'cols-grid');
  // three recessive gridlines + a darker baseline (brand §6.2)
  [1, 2 / 3, 1 / 3].forEach((f) => {
    const g = el('div', 'cols-gridline');
    g.style.bottom = `${f * 100}%`;
    g.append(el('span', 'cols-ytick mono', fmtN(Math.round(max * f))));
    grid.append(g);
  });
  const plot = el('div', 'cols-plot');
  rows.forEach((r) => {
    const c = el('div', 'col');
    const bar = el('div', 'col-fill');
    bar.style.height = `${(r.valor / max) * 100}%`;
    bar.title = `${r.etiqueta}: ${fmtN(r.valor)} ${etiquetaY}`;
    c.append(bar);
    if (r.marca) c.append(el('div', 'col-tick mono', r.marca));
    plot.append(c);
  });
  grid.append(plot);
  wrap.append(grid);
  parent.append(wrap);
}

/** A caveat rendered inline, at the size of the thing it qualifies — the project
    rule is that honesty is not a footnote. */
function nota(parent, texto, clase = '') {
  parent.append(el('p', `nota ${clase}`.trim(), texto));
}

// ── sections ─────────────────────────────────────────────────────────────────

function statrow(d) {
  const cob = d.cobertura;
  const lec = d.lectura || {};
  const row = $('statrow');
  const stats = [
    ['Sesiones del término', fmtN(cob.actas_en_termino)],
    ['Actas leídas', `${fmtN(cob.con_resumen)} de ${fmtN(cob.actas_en_termino)}`],
    ['Puntos analizados', fmtN(d.decisiones.n_puntos)],
    ['Texto leído', lec.proporcion != null ? fmtPct(lec.proporcion) : 'sin medir'],
  ];
  stats.forEach(([label, value]) => {
    const s = el('div', 'stat');
    s.append(el('span', 'stat-label', label), el('span', 'stat-value', value));
    row.append(s);
  });
}

/** T1 + N1. Deliberately first: the two coverages are the condition for reading
    every other section, so they are stated at full size, not as a disclaimer. */
function cobertura(d) {
  const c = $('c-cobertura');
  const cob = d.cobertura;
  const lec = d.lectura || {};
  const pctActas = cob.con_resumen / cob.actas_en_termino;

  const b1 = figura(c, {
    titulo: `Se han leído ${cob.con_resumen} de las ${cob.actas_en_termino} actas del término`
      + (lec.proporcion != null ? `, y de ellas el ${fmtPct(lec.proporcion)} de su texto` : ''),
    subtitulo: 'Dos coberturas distintas: cuántas actas se procesaron, y cuánto del texto de '
      + 'esas actas alcanzó a leer el modelo que redacta los resúmenes. Las gráficas de este '
      + 'panel se calculan sobre la primera; su precisión depende de la segunda.',
    fuente: 'Fuente: procesamiento propio sobre las actas del Ayuntamiento de Colima · umbral.mx',
  });

  // Reading depth is the page's single signal-coloured element (brand §3); the
  // actas-processed meter beside it stays in ink so the budget is not split.
  const medidores = el('div', 'medidores');
  [
    { lab: 'Actas procesadas', v: pctActas, tono: '',
      det: `${fmtN(cob.con_resumen)} de ${fmtN(cob.actas_en_termino)} actas` },
    { lab: 'Texto leído de esas actas', v: lec.proporcion, tono: 'signal',
      det: lec.proporcion != null
        ? `${fmtN(lec.chars_leidos)} de ${fmtN(lec.chars_ocr)} caracteres · `
          + `${fmtN(lec.actas_completas)} actas leídas completas`
        : 'sin medir en este lote' },
  ].forEach(({ lab, v, det, tono }) => {
    const m = el('div', 'medidor');
    m.append(el('div', 'medidor-lab', lab));
    const track = el('div', 'medidor-track');
    if (v != null) {                 // an unmeasured bar stays empty, not a sliver
      const fill = el('div', `medidor-fill ${tono}`.trim());
      fill.style.width = `${v * 100}%`;
      track.append(fill);
    }
    m.append(track);
    m.append(el('div', 'medidor-val mono', v != null ? fmtPct(v) : '—'));
    m.append(el('div', 'medidor-det', det));
    medidores.append(m);
  });
  b1.append(medidores);

  nota(c, cob.nota);
  if (lec.actas_sin_dato) {
    nota(c, `${fmtN(lec.actas_sin_dato)} acta(s) se resumieron antes de que se midiera la `
      + 'profundidad de lectura: no se les supone cobertura, se declaran sin dato.');
  }
  if (lec.ventanas_fallidas) {
    nota(c, `${fmtN(lec.ventanas_fallidas)} fragmento(s) de acta no pudieron resumirse; su `
      + 'parte se descuenta de la cobertura en vez de darse por leída.', 'nota-alert');
  }
  const conflictos = (lec.puntos_en_conflicto || []);
  if (conflictos.length) {
    nota(c, `${conflictos.length} punto(s) en que dos fragmentos del acta afirmaron resultados `
      + 'distintos: se resolvió por mayoría y se listan para verificarlos contra el PDF — '
      + conflictos.map((x) => `acta ${x.no_acta} punto ${x.punto}`).join(', ') + '.', 'nota-alert');
  }
}

/** I3 — the one section with full coverage: it reads the official index, not OCR. */
function cadencia(d) {
  const c = $('c-cadencia');
  const ses = (d.calendario?.sesiones || []).filter((s) => s.fecha);
  if (!ses.length) return;

  const porMes = new Map();
  ses.forEach((s) => {
    const k = s.fecha.slice(0, 7);
    porMes.set(k, (porMes.get(k) || 0) + 1);
  });
  const claves = [...porMes.keys()].sort();
  const rows = claves.map((k) => {
    const [y, m] = k.split('-');
    return {
      etiqueta: `${MESES[Number(m) - 1]} ${y}`,
      valor: porMes.get(k),
      marca: Number(m) === 1 ? y : (porMes.size <= 24 ? MESES[Number(m) - 1][0] : ''),
    };
  });
  const vals = rows.map((r) => r.valor);
  const meses = rows.length;
  const media = ses.length / meses;

  const body = figura(c, {
    titulo: `El cabildo sesionó ${fmtN(ses.length)} veces en ${fmtN(meses)} meses — `
      + `entre ${Math.min(...vals)} y ${Math.max(...vals)} veces por mes`,
    subtitulo: `Colima, ${fmtFecha(ses[0].fecha)} a ${fmtFecha(ses[ses.length - 1].fecha)}. `
      + `Promedio de ${media.toFixed(1)} sesiones por mes. Esta sección se calcula sobre el `
      + 'índice oficial y cubre las 74 sesiones del término, procesadas o no.',
    fuente: 'Fuente: índice de actas de cabildo, Ayuntamiento de Colima · umbral.mx',
  });
  columnas(body, rows, { etiquetaY: 'sesiones' });
  tablaDatos(c, [
    { label: 'Mes', get: (r) => r.etiqueta },
    { label: 'Sesiones', num: true, get: (r) => fmtN(r.valor) },
  ], rows, 'Ver sesiones por mes');
  nota(c, d.calendario.nota);
}

/** D2 (absorbs I2). Computed over the processed actas only, and says so. */
function categorias(d) {
  const c = $('c-categorias');
  const dec = d.decisiones;
  const entradas = Object.entries(dec.por_categoria || {});
  if (!entradas.length) return;

  const total = entradas.reduce((a, [, n]) => a + n, 0);
  const rows = entradas
    .map(([k, n]) => ({ etiqueta: CATEGORIA_ES[k] || k, valor: n, clave: k }))
    .sort((a, b) => b.valor - a.valor);
  const top3 = rows.filter((r) => r.clave !== 'tramite').slice(0, 3);
  const shareTop3 = top3.reduce((a, r) => a + r.valor, 0) / total;

  const etiquetasTop = top3.map((r, i) => (i === 0 ? r.etiqueta : r.etiqueta.toLowerCase()));
  const body = figura(c, {
    titulo: `${etiquetasTop.join(', ')} concentran ${fmtPct(shareTop3)} de los asuntos de fondo`,
    subtitulo: `${fmtN(total)} puntos de ${fmtN(d.cobertura.con_resumen)} actas leídas (de `
      + `${fmtN(d.cobertura.actas_en_termino)} del término). Quedan fuera los puntos de mero `
      + 'trámite de sesión —lista de asistencia, quórum, lectura del órden, clausura—; la '
      + 'categoría «trámite interno» agrupa los asuntos de procedimiento que sí se sometieron '
      + 'a votación.',
    fuente: 'Fuente: resúmenes generados sobre el OCR de las actas · umbral.mx',
  });
  barrasH(body, rows, { total });
  tablaDatos(c, [
    { label: 'Categoría', get: (r) => r.etiqueta },
    { label: 'Puntos', num: true, get: (r) => fmtN(r.valor) },
    { label: 'Del total', num: true, get: (r) => fmtPct(r.valor / total, 1) },
  ], rows, 'Ver asuntos por categoría');

  // Outcome mix, with the unreadable share drawn as its own bar, never dropped.
  const sent = Object.entries(dec.por_sentido || {});
  if (sent.length) {
    const tot = sent.reduce((a, [, n]) => a + n, 0);
    const rowsS = sent
      .map(([k, n]) => ({ etiqueta: SENTIDO_ES[k] || k, valor: n, clave: k }))
      .sort((a, b) => b.valor - a.valor);
    const nd = (dec.por_sentido.no_determinable || 0) / tot;
    // The gloss on «sin resultado legible» is printed only when that bar exists;
    // explaining an absent category is how a caveat becomes noise.
    const hayND = (dec.por_sentido.no_determinable || 0) > 0;
    const body2 = figura(c, {
      titulo: nd > 0.15
        ? `El resultado no se alcanza a leer en ${fmtPct(nd)} de los puntos`
        : `El acta declara el resultado en ${fmtPct(1 - nd)} de los puntos`,
      subtitulo: `${fmtN(tot)} puntos sustantivos de ${fmtN(d.cobertura.con_resumen)} actas `
        + `leídas de ${fmtN(d.cobertura.actas_en_termino)}.`
        + (hayND
          ? ' «Sin resultado legible» no significa que el cabildo no resolviera: significa que '
            + 'el texto disponible no permite afirmarlo, y por eso no se cuenta como aprobado '
            + 'ni como rechazado.'
          : ' Es el resultado que cada acta asienta; se cuenta sólo lo que declara.'),
      fuente: 'Fuente: resúmenes generados sobre el OCR de las actas · umbral.mx',
    });
    barrasH(body2, rowsS, { total: tot });
    if (nd > 0.15) {
      nota(c, 'Mientras esa proporción siga alta, este panel no publica una «tasa de '
        + 'aprobación»: calcularla sólo sobre lo legible daría una cifra que se leería como si '
        + 'fuera del cabildo entero.', 'nota-alert');
    }
  }
}

/** M4 — the amounts the actas state, largest first. Never a synthesized total
    presented as the budget; the double-count guard is disclosed inline. */
function montos(d, urlPorActa) {
  const c = $('c-montos');
  const m = d.montos;
  if (!m || !m.n_con_valor) return;

  const mayores = (m.mayores || []).slice(0, 10);
  const body = figura(c, {
    // The headline amount is written out in full: an abbreviation is where a
    // public money figure loses its meaning.
    titulo: `La decisión económica más grande que declaran las actas leídas es de `
      + `${fmtMXN(mayores[0]?.valor_mxn)}`,
    subtitulo: `${fmtN(m.n_con_valor)} cantidades con cifra, en ${fmtN(d.cobertura.con_resumen)} `
      + `actas leídas de ${fmtN(d.cobertura.actas_en_termino)}. Son los montos que el acta `
      + 'enuncia de forma explícita, no un presupuesto ni un gasto ejercido.',
    fuente: 'Fuente: montos declarados en las actas · umbral.mx',
  });
  barrasH(body, mayores.map((x) => ({
    etiqueta: `Acta ${x.no_acta} · punto ${x.punto}`,
    valor: x.valor_mxn,
    texto: fmtMXNCorto(x.valor_mxn),
    titulo: x.texto,
  })));

  const tot = el('p', 'total-declarado');
  tot.append(el('span', 'total-lab', 'Suma de lo declarado en las actas leídas'));
  tot.append(el('span', 'total-val mono', fmtMXN(m.suma_declarada_mxn)));
  c.append(tot);
  // The payload's own `nota` names its fields — useful to whoever reads the JSON,
  // jargon to whoever reads the page. Same caveat, said plainly.
  nota(c, 'Es la suma de las cantidades que las actas leídas enuncian de forma explícita. '
    + 'No es el presupuesto del municipio, ni su gasto total, ni dinero cuyo ejercicio se haya '
    + 'verificado: es lo que estas actas nombran. Cuando un punto declara el total de un '
    + 'paquete de obra y además el desglose obra por obra, se cuenta sólo el total, para no '
    + 'sumar dos veces los mismos pesos.');

  (m.puntos_total_y_desglose || []).forEach((p) => {
    nota(c, `Acta ${p.no_acta}, punto ${p.punto}: el acta declara un total de `
      + `${fmtMXN(p.total_mxn)} y además ${fmtN(p.n_componentes)} obras que suman `
      + `${fmtMXN(p.suma_componentes_mxn)}. Se cuenta sólo el total, para no sumar dos veces `
      + 'los mismos pesos.');
  });

  tablaDatos(c, [
    { label: 'Acta', get: (r) => `Acta ${r.no_acta}` },
    { label: 'Punto', num: true, get: (r) => String(r.punto) },
    { label: 'Cifra en el acta', get: (r) => r.texto },
    { label: 'Pesos', num: true, get: (r) => fmtMXN(r.valor_mxn) },
    // Every figure has to be checkable against the scan it came from.
    { label: 'Acta original',
      get: (r) => {
        const u = urlPorActa.get(r.acta);
        if (!u) return 'sin enlace';
        const a = el('a', null, 'Ver el PDF');
        a.href = u;
        a.rel = 'external';
        a.setAttribute('aria-label', `Ver el PDF del acta ${r.no_acta}`);
        return a;
      } },
  ], mayores, 'Ver las cantidades y su acta');
}

/** P1 (+P5). The breakdown of states lives in the table, not in four hues that
    this palette cannot separate for colour-blind readers. */
function asistencia(d) {
  const c = $('c-asistencia');
  const a = d.asistencia;
  if (!a || !a.por_integrante?.length) return;

  const con = a.por_integrante.filter((p) => p.tasa_asistencia != null);
  const rows = [...con].sort((x, y) => y.tasa_asistencia - x.tasa_asistencia);
  const media = con.reduce((s, p) => s + p.tasa_asistencia, 0) / (con.length || 1);
  const perfectos = con.filter((p) => p.tasa_asistencia === 1).length;

  const body = figura(c, {
    titulo: perfectos === con.length
      ? `Los ${fmtN(con.length)} integrantes asistieron a todas las sesiones leídas`
      : `${fmtN(perfectos)} de ${fmtN(con.length)} integrantes asistieron a todas las sesiones leídas`,
    subtitulo: `Pase de lista de ${fmtN(a.sesiones_consideradas)} sesiones de `
      + `${fmtN(d.cobertura.actas_en_termino)} del término. Asistencia promedio `
      + `${fmtPct(media, 1)}. Cuenta como asistencia la presencia física y la remota.`,
    fuente: 'Fuente: pase de lista de cada acta · umbral.mx',
  });
  barrasH(body, rows.map((p) => ({
    etiqueta: p.nombre,
    valor: p.tasa_asistencia,
    texto: fmtPct(p.tasa_asistencia, 1),
    titulo: `${p.cargo} · ${p.asistio} de ${p.sesiones} sesiones`,
  })));

  tablaDatos(c, [
    { label: 'Integrante', get: (r) => r.nombre },
    { label: 'Cargo', get: (r) => r.cargo },
    { label: 'Asistió', num: true, get: (r) => fmtN(r.asistio) },
    { label: 'Falta justificada', num: true, get: (r) => fmtN(r.falta_justificada) },
    { label: 'Ausente', num: true, get: (r) => fmtN(r.ausente) },
    { label: 'Sin determinar', num: true, get: (r) => fmtN(r.no_determinable) },
    { label: 'Asistencia', num: true, get: (r) => (r.tasa_asistencia != null ? fmtPct(r.tasa_asistencia, 1) : '—') },
  ], a.por_integrante, 'Ver el pase de lista por integrante');
  nota(c, 'La asistencia se calcula sólo sobre las sesiones en que el pase de lista se '
    + 'alcanza a leer: cuando el escaneo no lo permite, esa sesión no cuenta ni como '
    + 'presencia ni como falta para nadie.');

  (a.suplencias || []).forEach((s) => {
    nota(c, `Suplencia: en el acta ${s.no_acta} (${fmtFecha(s.fecha)}) el pase de lista nombra a `
      + `${s.nombre}, que no corresponde a ningún integrante del cabildo. Se reporta tal cual, `
      + 'sin asignarlo a la silla de nadie.');
  });
}

/** G1 + N2 — the question the project started from, answered as a list rather
    than a chart: "what got decided in my neighbourhood?" */
function colonias(d) {
  const c = $('c-colonias');
  const cols = d.colonias || [];
  if (!cols.length) return;

  const body = figura(c, {
    titulo: `Las actas leídas mencionan ${fmtN(cols.length)} colonias, fraccionamientos o `
      + 'localidades',
    subtitulo: `De ${fmtN(d.cobertura.con_resumen)} actas leídas de `
      + `${fmtN(d.cobertura.actas_en_termino)}. Es una lista de menciones, no un censo: que `
      + 'una colonia no aparezca no significa que el cabildo no haya decidido nada sobre ella, '
      + 'sino que ninguna de las actas leídas la nombra.',
    fuente: 'Fuente: colonias nombradas en las actas · umbral.mx',
  });

  const buscador = el('div', 'col-buscador');
  const input = el('input');
  input.type = 'search';
  input.placeholder = 'Filtrar por colonia — p. ej. Fátima';
  input.setAttribute('aria-label', 'Filtrar colonias');
  buscador.append(input);
  body.append(buscador);

  // Shown in full on request rather than inside a scrolling box: an inner
  // scroller swallows the page scroll when the cursor is over it.
  const TOPE = 12;
  const lista = el('ul', 'colonia-list');
  const masBtn = el('button', 'btn-secondary col-mas');
  masBtn.type = 'button';
  let todas = false;

  const pinta = (filtro) => {
    lista.textContent = '';
    const f = filtro.trim().toLowerCase();
    const vis = cols.filter((x) => !f || x.nombre.toLowerCase().includes(f));
    if (!vis.length) {
      masBtn.hidden = true;
      lista.append(el('li', 'colonia-vacio',
        'Ninguna de las actas leídas menciona una colonia con ese nombre. Puede que la '
        + 'decisión exista en un acta que aún no se ha procesado.'));
      return;
    }
    const mostradas = (todas || f) ? vis : vis.slice(0, TOPE);
    mostradas.forEach((x) => {
      const li = el('li', 'colonia-item');
      li.append(el('span', 'colonia-nombre', x.nombre));
      li.append(el('span', 'colonia-n mono',
        `${fmtN(x.menciones)} ${x.menciones === 1 ? 'mención' : 'menciones'}`));
      lista.append(li);
    });
    const oculta = vis.length - mostradas.length;
    masBtn.hidden = !(oculta > 0 || (todas && !f));
    masBtn.textContent = oculta > 0
      ? `Ver las ${fmtN(vis.length)} colonias` : 'Ver sólo las más mencionadas';
  };
  masBtn.addEventListener('click', () => { todas = !todas; pinta(input.value); });
  pinta('');
  input.addEventListener('input', () => pinta(input.value));
  body.append(lista, masBtn);
}

/** T3 — gaps in the source, declared and not imputed. */
function integridad(d) {
  const g = d.integridad;
  const c = $('c-integridad');
  if (!g) return;

  const hallazgos = [];
  if (g.huecos_de_numeracion?.length) {
    hallazgos.push(`El índice oficial no publica el acta ${g.huecos_de_numeracion.join(', ')} `
      + 'del término: el número existe en la secuencia pero la sesión no aparece.');
  }
  if (g.numeros_duplicados?.length) {
    hallazgos.push(`La fuente asigna el número ${g.numeros_duplicados.join(', ')} a dos sesiones `
      + 'distintas, con fechas distintas. Se conservan ambas; no se renumera ninguna.');
  }
  if (g.sin_agenda_publicada?.length) {
    hallazgos.push(`${g.sin_agenda_publicada.length} sesión(es) sin órden del día en el índice.`);
  }
  if (g.sin_enlace_pdf?.length) {
    hallazgos.push(`${g.sin_enlace_pdf.length} sesión(es) sin enlace al PDF.`);
  }
  if (g.sin_fecha_publicada?.length) {
    hallazgos.push(`${g.sin_fecha_publicada.length} sesión(es) sin fecha publicada.`);
  }

  figura(c, {
    titulo: hallazgos.length
      ? `El expediente del término tiene ${fmtN(hallazgos.length)} inconsistencia(s) de origen`
      : 'El expediente del término está completo en el índice oficial',
    subtitulo: `${fmtN(g.actas_en_termino)} sesiones. Lo que falta o no cuadra en la fuente se `
      + 'declara aquí y se conserva así en los datos: no se rellena por inferencia.',
    fuente: 'Fuente: índice de actas de cabildo, Ayuntamiento de Colima · umbral.mx',
  });
  if (hallazgos.length) {
    const ul = el('ul', 'hallazgos');
    hallazgos.forEach((h) => ul.append(el('li', null, h)));
    c.append(ul);
  } else {
    nota(c, 'Las 74 sesiones tienen número, fecha, órden del día y enlace al PDF.');
  }
  nota(c, g.nota);
}

// ── boot ─────────────────────────────────────────────────────────────────────
async function main() {
  let d;
  try {
    const r = await fetch(`analytics-${TERMINO}.json`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    d = await r.json();
  } catch (e) {
    const m = $('c-cobertura');
    if (m) m.append(el('p', 'nota nota-alert',
      'No se pudo cargar el archivo de analítica. El panel se genera junto con el '
      + 'procesamiento de las actas; si acabas de clonar el repositorio, corre '
      + 'processor/build_analytics.py.'));
    return;
  }

  $('termino').textContent = d.termino || TERMINO;
  const urlPorActa = new Map((d.calendario?.sesiones || []).map((s) => [s.acta, s.pdf_url]));

  statrow(d);
  cobertura(d);
  cadencia(d);
  categorias(d);
  montos(d, urlPorActa);
  asistencia(d);
  colonias(d);
  integridad(d);
}

main();
