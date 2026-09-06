---
title: Panel por administración · Cabildo de Colima
---

```js
// Bloque 1 — cromo de la página. No espera red.
// Framework fusiona todos los `import` de un mismo bloque en UNA celda, que
// resuelve cuando resuelve su importación más lenta. Separarlos por lo que
// esperan hace que la marca pinte en cuanto llega su módulo, en vez de
// esperar detrás del archivo de datos (docs/framework-notes.md §1).
import "./components/fonts.js";
import {brand, nav, label, dots, meta} from "./components/chrome.js";
```

```js
// Bloque 2 — funciones puras. No espera red.
import {chartFrame, figureRow, dataTable} from "./components/frame.js";
import {barrasH, columnas, medidor} from "./components/charts.js";
import {fmt, fmtPct, fmtMXN, fmtMXNCorto, fmtFecha, textoMeta, CATEGORIA_ES, SENTIDO_ES} from "./components/format.js";
```

```js
// Bloque 3 — el único que espera datos.
const d = await FileAttachment("data/analytics.json").json();
```

```js
// La fecha de consulta sale del payload, nunca escrita a mano: así sigue al
// procesamiento en vez de separarse de él (UMB-CHT-003, ISO por UMB-NUM-003).
const consultado = (d.generado ?? "").slice(0, 10);
const cob = d.cobertura;
const lec = d.lectura;
const TERMINO = d.termino;
```

<div>${brand()}</div>
<div>${nav()}</div>

```js
// La cápsula sale del payload: cuándo se procesó y hasta dónde llegan los datos.
const sesionesConFecha = (d.calendario?.sesiones ?? []).map((x) => x.fecha).filter(Boolean).sort();
const ultimaSesion = sesionesConFecha[sesionesConFecha.length - 1];
```

<div>${meta(textoMeta(d.generado, ultimaSesion))}</div>

# Panel por administración

<div>${dots()}</div>

<p class="u-standfirst">
Qué tipo de decisiones tomó este cabildo, cuánto dinero nombró, quién asistió y con
qué frecuencia sesionó. Cada cifra dice sobre cuántas actas se calculó: el análisis
avanza por lotes y ninguna gráfica supone más de lo que se ha leído.
</p>

```js
figureRow([
  {label: "actas del término", value: cob.actas_en_termino},
  {label: "actas leídas", value: cob.con_resumen},
  {label: "puntos analizados", value: d.decisiones.n_puntos},
  {label: "texto leído", value: lec.proporcion != null ? fmtPct(lec.proporcion, 1) : "sin medir"}
])
```

<section class="u-section">

```js
label("cobertura del análisis")
```

```js
chartFrame({
  title: lec.proporcion != null
    ? `Se han leído ${cob.con_resumen} de las ${cob.actas_en_termino} actas del término, y de ellas el ${fmtPct(lec.proporcion)} de su texto`
    : `Se han leído ${cob.con_resumen} de las ${cob.actas_en_termino} actas del término`,
  subtitle: `Proporción de actas resumidas y proporción del texto leído en cada una, término ${TERMINO}. `
    + `Son dos coberturas distintas: cuántas actas se procesaron, y cuánto del texto de esas actas `
    + `alcanzó a leer el modelo que redacta los resúmenes. Las gráficas de este panel se calculan `
    + `sobre la primera; su precisión depende de la segunda.`,
  source: "Elaboración propia con el OCR de las actas de cabildo del Ayuntamiento de Colima",
  consultado,
  plot: medidor([
    {etiqueta: "actas resumidas", valor: cob.con_resumen / cob.actas_en_termino, signal: false},
    {etiqueta: "texto leído por acta", valor: lec.proporcion ?? 0, signal: true}
  ]),
  data: [
    {medida: "actas resumidas", valor: cob.con_resumen, base: cob.actas_en_termino,
     proporcion: cob.con_resumen / cob.actas_en_termino},
    {medida: "texto leído (caracteres)", valor: lec.chars_leidos, base: lec.chars_ocr,
     proporcion: lec.proporcion}
  ],
  columns: ["medida", "valor", "base", "proporcion"],
  numericColumns: ["valor", "base", "proporcion"],
  download: `cobertura-${TERMINO}.csv`,
  note: cob.nota
})
```

```js
// Los huecos se dibujan como huecos: si una ventana de lectura falló, su
// parte se descuenta de la cobertura en vez de darse por leída.
lec.ventanas_fallidas > 0
  ? html`<p class="u-note u-note--alert">${fmt(lec.ventanas_fallidas)} fragmento(s) de acta no
      pudieron resumirse; su parte se descuenta de la cobertura en vez de darse por leída.</p>`
  : html``
```

```js
(lec.puntos_en_conflicto?.length ?? 0) > 0
  ? html`<p class="u-note u-note--alert">${lec.puntos_en_conflicto.length} punto(s) en que dos
      fragmentos del acta afirmaron resultados distintos; se marcan para revisión en vez de
      resolverse por desempate silencioso: ${lec.puntos_en_conflicto
        .map((x) => `acta ${x.no_acta} punto ${x.punto}`).join(", ")}.</p>`
  : html``
```

</section>

<section class="u-section">

```js
label("cadencia de sesiones")
```

```js
const ses = [...d.calendario.sesiones].filter((s) => s.fecha).sort((a, b) => a.fecha.localeCompare(b.fecha));
const porMes = d3.rollups(ses, (v) => v.length, (s) => s.fecha.slice(0, 7))
  .sort((a, b) => a[0].localeCompare(b[0]))
  .map(([mes, n]) => ({mes, sesiones: n}));
const vals = porMes.map((r) => r.sesiones);
const media = vals.reduce((a, b) => a + b, 0) / (vals.length || 1);
```

```js
chartFrame({
  title: `El cabildo sesionó ${fmt(ses.length)} veces en ${fmt(porMes.length)} meses — entre ${Math.min(...vals)} y ${Math.max(...vals)} veces por mes`,
  subtitle: `Conteo de sesiones por mes, Colima, ${fmtFecha(ses[0].fecha)} a ${fmtFecha(ses[ses.length - 1].fecha)}. `
    + `Promedio de ${media.toFixed(1)} sesiones por mes. Esta sección se calcula sobre el índice `
    + `oficial y cubre las ${fmt(d.integridad.actas_en_termino)} sesiones del término, procesadas o no.`,
  source: "Elaboración propia con datos del índice de actas de cabildo del Ayuntamiento de Colima",
  consultado,
  plot: columnas(porMes, {x: "mes", y: "sesiones"}),
  data: porMes,
  columns: ["mes", "sesiones"],
  numericColumns: ["sesiones"],
  download: `cadencia-${TERMINO}.csv`,
  note: d.calendario.nota
})
```

</section>

<section class="u-section">

```js
label("mezcla de asuntos")
```

```js
const cats = Object.entries(d.decisiones.por_categoria)
  .map(([k, n]) => ({categoria: CATEGORIA_ES[k] ?? k, puntos: n}))
  .sort((a, b) => b.puntos - a.puntos);
const totalCat = cats.reduce((a, b) => a + b.puntos, 0);
const top3 = cats.slice(0, 3);
const shareTop3 = top3.reduce((a, b) => a + b.puntos, 0) / totalCat;
```

```js
chartFrame({
  title: `${top3.map((c) => c.categoria.toLowerCase()).join(", ")} concentran ${fmtPct(shareTop3)} de los asuntos`,
  subtitle: `Distribución de los puntos por categoría de asunto, término ${TERMINO}. `
    + `${fmt(totalCat)} puntos de ${fmt(cob.con_resumen)} actas leídas (de ${fmt(cob.actas_en_termino)} `
    + `del término). La categoría «trámite interno» agrupa los asuntos de procedimiento que sí se `
    + `sometieron a votación.`,
  source: "Elaboración propia con los resúmenes generados sobre el OCR de las actas de cabildo del Ayuntamiento de Colima",
  consultado,
  plot: barrasH(cats, {x: "puntos", y: "categoria"}),
  data: cats,
  columns: ["categoria", "puntos"],
  numericColumns: ["puntos"],
  download: `categorias-${TERMINO}.csv`,
  note: d.decisiones.base_tier_a
})
```

```js
const sentidos = Object.entries(d.decisiones.por_sentido)
  .map(([k, n]) => ({sentido: SENTIDO_ES[k] ?? k, puntos: n, clave: k}))
  .sort((a, b) => b.puntos - a.puntos);
const totalSent = sentidos.reduce((a, b) => a + b.puntos, 0);
const nd = (d.decisiones.por_sentido.no_determinable ?? 0) / totalSent;
```

```js
chartFrame({
  title: nd > 0.15
    ? `El resultado no se alcanza a leer en ${fmtPct(nd)} de los puntos`
    : `El acta declara el resultado en ${fmtPct(1 - nd)} de los puntos`,
  subtitle: `Distribución de los puntos sustantivos por sentido de la resolución, término ${TERMINO}. `
    + `${fmt(totalSent)} puntos de ${fmt(cob.con_resumen)} actas leídas de ${fmt(cob.actas_en_termino)}.`,
  source: "Elaboración propia con los resúmenes generados sobre el OCR de las actas de cabildo del Ayuntamiento de Colima",
  consultado,
  plot: barrasH(sentidos, {x: "puntos", y: "sentido"}),
  data: sentidos.map(({sentido, puntos}) => ({sentido, puntos})),
  columns: ["sentido", "puntos"],
  numericColumns: ["puntos"],
  download: `sentido-${TERMINO}.csv`,
  note: "«Sin resultado legible» no significa que el cabildo no resolviera: significa que el texto "
    + "disponible no permite afirmarlo, y por eso no se cuenta como aprobado ni como rechazado."
})
```

</section>

<section class="u-section">

```js
label("dinero declarado")
```

```js
const m = d.montos;
const mayores = m.mayores.map((x) => ({
  asunto: `Acta ${x.no_acta} · punto ${x.punto}`,
  monto: x.valor_mxn
})).filter((x) => x.monto != null);
```

```js
chartFrame({
  title: `La decisión económica más grande que declaran las actas leídas es de ${fmtMXN(m.mayores[0]?.valor_mxn)}`,
  subtitle: `Montos que las actas enuncian de forma explícita, ordenados de mayor a menor, en pesos `
    + `corrientes, término ${TERMINO}. ${fmt(m.n_con_valor)} cantidades con cifra, en `
    + `${fmt(cob.con_resumen)} actas leídas de ${fmt(cob.actas_en_termino)}. No son un presupuesto `
    + `ni un gasto ejercido.`,
  source: "Elaboración propia con los montos declarados en las actas de cabildo del Ayuntamiento de Colima",
  consultado,
  plot: barrasH(mayores, {x: "monto", y: "asunto", formatoX: fmtMXNCorto}),
  data: m.mayores,
  columns: ["no_acta", "punto", "texto", "valor_mxn"],
  numericColumns: ["no_acta", "punto", "valor_mxn"],
  download: `montos-${TERMINO}.csv`,
  note: m.nota
})
```

```js
html`<p class="u-note">Es la suma de las cantidades que las actas leídas enuncian de forma
explícita: <strong>${fmtMXN(m.suma_declarada_mxn)}</strong>. No es el presupuesto del municipio
ni su gasto ejercido, y no debe leerse como un total oficial.</p>`
```

```js
// Un punto que declara un total y su desglose contaría dos veces si se
// sumaran ambos. El guard se revela en pantalla en vez de resolverse callado.
(m.puntos_total_y_desglose?.length ?? 0) > 0
  ? html`<p class="u-note u-note--alert">En ${m.puntos_total_y_desglose.length} punto(s) el acta
      declara un total y también su desglose. Sólo se cuenta una vez; sumar ambos inflaría la
      cifra.</p>`
  : html``
```

</section>

<section class="u-section">

```js
label("asistencia del cabildo")
```

```js
const a = d.asistencia;
const con = a.por_integrante.filter((p) => p.sesiones > 0);
const asis = [...con]
  .map((p) => ({integrante: p.nombre, tasa: p.tasa_asistencia}))
  .sort((x, y) => y.tasa - x.tasa);
const perfectos = con.filter((p) => p.tasa_asistencia === 1).length;
const mediaAsis = con.reduce((s, p) => s + p.tasa_asistencia, 0) / (con.length || 1);
```

```js
chartFrame({
  title: perfectos === con.length
    ? `Los ${fmt(con.length)} integrantes asistieron a todas las sesiones leídas`
    : `${fmt(perfectos)} de ${fmt(con.length)} integrantes asistieron a todas las sesiones leídas`,
  subtitle: `Tasa de asistencia por integrante sobre las sesiones con pase de lista legible, `
    + `término ${TERMINO}. ${fmt(a.sesiones_consideradas)} sesiones de ${fmt(cob.actas_en_termino)} `
    + `del término. Asistencia promedio ${fmtPct(mediaAsis, 1)}. Cuenta como asistencia la `
    + `presencia física y la remota.`,
  source: "Elaboración propia con el pase de lista de cada acta de cabildo del Ayuntamiento de Colima",
  consultado,
  plot: barrasH(asis, {x: "tasa", y: "integrante", formatoX: (v) => `${(v * 100).toFixed(0)}%`}),
  data: a.por_integrante,
  columns: ["nombre", "cargo", "sesiones", "asistio", "presente", "remoto", "falta_justificada", "ausente", "no_determinable", "tasa_asistencia"],
  numericColumns: ["sesiones", "asistio", "presente", "remoto", "falta_justificada", "ausente", "no_determinable", "tasa_asistencia"],
  download: `asistencia-${TERMINO}.csv`,
  note: a.nota
})
```

```js
// Una suplencia se reporta tal cual: el acta sienta a alguien que no está en
// el roster, y forzarlo a una silla sería inventar (regla de no imputar).
(a.suplencias?.length ?? 0) > 0
  ? html`<div><p class="u-note">Suplencias que el pase de lista nombra y que no corresponden a
      ningún integrante del roster. Se reportan literalmente, sin asignarlas a nadie.</p>
      ${dataTable(a.suplencias, {columns: ["no_acta", "fecha", "nombre"], numericColumns: ["no_acta"]})}</div>`
  : html``
```

</section>

<section class="u-section">

```js
label("qué se decidió en mi colonia")
```

```js
const cols = d.colonias ?? [];
const filtro = view(Inputs.search(cols, {
  placeholder: "Filtrar por colonia — p. ej. Fátima",
  label: null,
  format: null
}));
```

```js
chartFrame({
  title: `Las actas leídas mencionan ${fmt(cols.length)} colonias, fraccionamientos o localidades`,
  subtitle: `Conteo de menciones por colonia en las actas leídas, término ${TERMINO}. De `
    + `${fmt(cob.con_resumen)} actas leídas de ${fmt(cob.actas_en_termino)}.`,
  source: "Elaboración propia con las colonias nombradas en las actas de cabildo del Ayuntamiento de Colima",
  consultado,
  plot: barrasH(
    [...filtro].sort((a, b) => b.menciones - a.menciones).slice(0, 15)
      .map((x) => ({colonia: x.nombre, menciones: x.menciones})),
    {x: "menciones", y: "colonia"}
  ),
  data: [...filtro].sort((a, b) => b.menciones - a.menciones),
  columns: ["nombre", "menciones"],
  numericColumns: ["menciones"],
  download: `colonias-${TERMINO}.csv`,
  note: "Es una lista de menciones, no un censo: que una colonia no aparezca no significa que el "
    + "cabildo no haya decidido nada sobre ella, sino que ninguna de las actas leídas la nombra. "
    + "La gráfica muestra las 15 más mencionadas del filtro; la tabla, todas."
})
```

</section>

<section class="u-section">

```js
label("integridad del expediente")
```

```js
const g = d.integridad;
const hallazgos = [];
if (g.sin_agenda_publicada?.length) hallazgos.push(`${g.sin_agenda_publicada.length} sesión(es) sin órden del día en el índice oficial.`);
if (g.sin_enlace_pdf?.length) hallazgos.push(`${g.sin_enlace_pdf.length} sesión(es) sin enlace al PDF.`);
if (g.sin_fecha_publicada?.length) hallazgos.push(`${g.sin_fecha_publicada.length} sesión(es) sin fecha publicada.`);
if (g.huecos_de_numeracion?.length) hallazgos.push(`La numeración de la fuente salta: falta ${g.huecos_de_numeracion.join(", ")}.`);
if (g.numeros_duplicados?.length) hallazgos.push(`La fuente asigna el número ${g.numeros_duplicados.join(", ")} a dos sesiones distintas.`);
```

```js
chartFrame({
  title: hallazgos.length
    ? `El expediente del término tiene ${fmt(hallazgos.length)} inconsistencia(s) de origen`
    : "El expediente del término está completo en el índice oficial",
  subtitle: `Conteo de inconsistencias del índice oficial, término ${TERMINO}. `
    + `${fmt(g.actas_en_termino)} sesiones. Lo que falta o no cuadra en la fuente se declara aquí `
    + `y se conserva así en los datos: no se rellena por inferencia.`,
  source: "Elaboración propia con datos del índice de actas de cabildo del Ayuntamiento de Colima",
  consultado,
  plot: barrasH([
    {control: "con órden del día", sesiones: g.actas_en_termino - (g.sin_agenda_publicada?.length ?? 0)},
    {control: "con enlace al PDF", sesiones: g.actas_en_termino - (g.sin_enlace_pdf?.length ?? 0)},
    {control: "con fecha publicada", sesiones: g.actas_en_termino - (g.sin_fecha_publicada?.length ?? 0)}
  ], {x: "sesiones", y: "control"}),
  data: [
    {control: "sesiones en el término", sesiones: g.actas_en_termino},
    {control: "sin órden del día", sesiones: g.sin_agenda_publicada?.length ?? 0},
    {control: "sin enlace al PDF", sesiones: g.sin_enlace_pdf?.length ?? 0},
    {control: "sin fecha publicada", sesiones: g.sin_fecha_publicada?.length ?? 0},
    {control: "huecos de numeración", sesiones: g.huecos_de_numeracion?.length ?? 0},
    {control: "números duplicados", sesiones: g.numeros_duplicados?.length ?? 0}
  ],
  columns: ["control", "sesiones"],
  numericColumns: ["sesiones"],
  download: `integridad-${TERMINO}.csv`,
  note: g.nota
})
```

```js
hallazgos.length
  ? html`<ol class="u-caveats">${hallazgos.map((h) => html`<li>${h}</li>`)}</ol>`
  : html`<p class="u-note">Las ${fmt(g.actas_en_termino)} sesiones tienen número, fecha, órden del
      día y enlace al PDF.</p>`
```

</section>

<section class="u-section">

```js
label("cómo leer este panel")
```

Las cifras salen de dos fuentes distintas y conviene no confundirlas. La **cadencia de
sesiones** y la **integridad del expediente** se calculan sobre el índice oficial y cubren
todas las sesiones del término. Todo lo demás —asuntos, dinero, asistencia, colonias— se
extrae del texto de las actas, que son escaneos sin capa de texto: se pasan por OCR y un
modelo de lenguaje redacta el resumen y clasifica cada punto.

De ahí las dos coberturas que el panel declara arriba: *cuántas actas* se han procesado y
*cuánto del texto de cada una* alcanzó a leerse. Una gráfica calculada sobre una parte de
las actas no describe al cabildo del término: describe esa parte.

Los resúmenes y las clasificaciones son **generados por IA sobre texto OCR y pueden contener
errores**. Cuando el acta no declara con claridad un resultado, se marca como no determinable
en vez de inventarlo; los nombres que no corresponden a ningún integrante del cabildo se
reportan tal cual, sin asignarlos a nadie; y las cantidades son sólo las que el acta enuncia
de forma explícita — nunca un total calculado y presentado como oficial.

```js
html`<p class="u-source">Instantánea de los datos: ${consultado}. Cada gráfica declara esa misma
fecha de consulta en su línea de fuente · estructura y datos derivados CC BY 4.0 · código MIT ·
el texto de las actas es del Ayuntamiento de Colima y se atribuye a su fuente.</p>`
```

Cómo se construye este archivo, qué problemas hubo que resolver y qué no se puede medir:
[metodología pública](../metodologia.html).

</section>
