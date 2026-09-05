/**
 * Comprueba lo publicado montando las páginas de verdad, no leyéndolas.
 *
 * Esto es lo que `verificar_marca.py` no puede hacer: aquella puerta lee el
 * código fuente; ésta corre el JavaScript y mira el DOM que resulta. Las dos
 * hacen falta, porque un encuadre puede estar bien escrito y no llegar a
 * dibujarse.
 *
 * Un navegador daría falsos negativos —durante esta migración devolvió estilo
 * vacío para reglas que sí existen, y `docs/framework-notes.md` de
 * desaparecidosmx cuenta cómo devolvió marcos obsoletos dos veces— así que
 * donde el DOM no basta, se lee la regla CSS, no el estilo computado.
 *
 * Uso:
 *     python3 -m http.server 8765 --directory site &
 *     npm run verificar
 */
import {JSDOM} from "jsdom";
import {readFileSync, existsSync} from "node:fs";

const DIR = "site/";
const BASE = process.env.BASE ?? "http://localhost:8765/";
let bad = 0;
const fail = (m) => { bad++; console.log(`  ✗ ${m}`); };
const ok = (m) => console.log(`  ✓ ${m}`);

/**
 * Lee la retícula de puntos de una hoja, venga escrita o minificada.
 *
 * El empaquetador de Framework escribe `body:before` con un solo dos puntos y
 * `opacity:.55` sin el cero, así que comparar el texto tal cual daba una
 * diferencia donde no la hay. Se normaliza antes de comparar.
 */
function reticula(css) {
  const b = (css.match(/body::?before\s*\{([\s\S]*?)\}/) || [])[1] ?? "";
  const g = (n) => {
    const v = (b.match(new RegExp(`${n}\\s*:\\s*([^;}]+)`)) || [])[1]?.trim();
    if (v === undefined) return undefined;
    // `.55` y `0.55` son el mismo número; los espacios alrededor de una coma
    // tampoco cambian nada. Se compara el valor, no cómo se escribió.
    return v
      .replace(/(^|[\s(,])\.(\d)/g, "$10.$2")
      .replace(/\s*,\s*/g, ",")
      .replace(/\s+/g, " ")
      .trim();
  };
  return {opacity: g("opacity"), size: g("background-size"), image: g("background-image")};
}

/* ── 1. Las dos páginas estáticas ──────────────────────────────────────── */
for (const [page, script] of [["index.html", "app.js"], ["metodologia.html", "metodologia.js"]]) {
  console.log(`\n── ${page} (instrumento) ──`);
  const dom = new JSDOM(readFileSync(DIR + page, "utf8"),
    {url: BASE + page, runScripts: "outside-only", pretendToBeVisual: true});
  const w = dom.window;
  w.fetch = (u, o) => fetch(new URL(u, BASE).href, o);
  w.eval(readFileSync(DIR + script, "utf8"));
  await new Promise((r) => setTimeout(r, 1200));
  const d = w.document;

  // El encuadre 2.0.0: dos lados, sin licencia ni corte en la línea.
  const srcs = [...d.querySelectorAll(".fig-src")];
  for (const s of srcs) {
    const l = s.querySelector(".fig-src-origen"), r = s.querySelector(".fig-src-sitio");
    if (!l || !r) { fail(`línea de fuente sin dos lados: "${s.textContent.trim().slice(0, 50)}"`); continue; }
    const lt = l.textContent.trim();
    if (!lt.startsWith("Fuente: Elaboración propia")) fail(`izquierda: "${lt.slice(0, 50)}"`);
    if (!/Consulta realizada el \d{4}-\d{2}-\d{2}\./.test(lt)) fail("sin fecha de consulta ISO");
    if (r.textContent.trim() !== "umbral.org.mx") fail(`derecha: "${r.textContent.trim()}"`);
    if (/CC BY|MIT/i.test(s.textContent)) fail("la licencia sigue en la gráfica (UMB-DAT-004)");
  }
  ok(`${srcs.length} línea(s) de fuente a dos lados`);

  if (!/CC BY 4\.0/.test(d.body.textContent)) fail("la página no declara la licencia");
  if (/umbral\.mx(?!\w)/.test(d.body.textContent.replace(/umbral\.org\.mx/g, ""))) fail("umbral.mx sigue en pantalla");
  ok("licencia en la página · dominio umbral.org.mx");

  // Todo el instrumento va en modo instrumento, y el atributo tiene que venir
  // en el HTML: si lo pusiera el JavaScript, la página parpadearía en claro
  // antes de oscurecerse.
  d.documentElement.dataset.mode === "instrumento"
    ? ok('data-mode="instrumento" en el HTML')
    : fail(`la página no declara modo instrumento (data-mode="${d.documentElement.dataset.mode ?? ""}")`);
  // El isotipo claro sobre fondo oscuro es el archivo `-dark`.
  const iso = d.querySelector(".u-brand img");
  if (iso && /isotype-light/.test(iso.getAttribute("src") ?? "")) fail("isotipo de fondo claro sobre fondo oscuro");

  // Mismas medidas y mismo encabezado que el panel. Antes esta hoja tenía una
  // columna de 880px y el panel 1200/1080: pasar de una página a la otra movía
  // el contenido, y un instrumento con dos anchos son dos instrumentos.
  // Se leen las REGLAS, no el estilo computado: jsdom no resuelve `var()` desde
  // una hoja externa y devolvería `none` para un max-width que sí existe. Es la
  // misma trampa que con font-weight, y la razón de no fiarse de un navegador
  // para esto (docs/framework-notes.md §11).
  if (!d.querySelector(".u-sheet")) fail("la página no está montada sobre .u-sheet");
  const hoja = readFileSync(DIR + "styles.css", "utf8");
  const tok = (n) => (hoja.match(new RegExp(`${n}:\\s*([^;]+)`)) || [])[1]?.trim();
  const medidas = {"--u-sheet": "1200px", "--u-column": "1080px", "--u-edge": "32px"};
  const malas = Object.entries(medidas).filter(([k, v]) => tok(k) !== v);
  malas.length
    ? malas.forEach(([k, v]) => fail(`${k} es ${tok(k) ?? "—"}, se esperaba ${v}`))
    : ok(`hoja ${tok("--u-sheet")}, columna ${tok("--u-column")}, margen ${tok("--u-edge")}`);
  if (!/\.u-sheet\s*\{[^}]*max-width:\s*var\(--u-sheet\)/.test(hoja)) fail(".u-sheet no usa --u-sheet");
  if (!/^main\s*\{[^}]*max-width:\s*var\(--u-column\)/m.test(hoja)) fail("main no usa --u-column");

  // La retícula de puntos tiene que pesar lo mismo en las dos superficies. La
  // opacidad faltaba aquí y estaba en el panel, así que los puntos del margen
  // cambiaban de peso al navegar. Es mobiliario (UMB-LAY-009): tiene que
  // desaparecer igual en las dos.
  const r = reticula(hoja);
  r.opacity === "0.55"
    ? ok(`retícula: opacidad ${r.opacity}, paso ${r.size}`)
    : fail(`la retícula tiene opacidad ${r.opacity ?? "sin declarar"}, el panel usa 0.55`);

  // Sin barra de encabezado: la marca y las pestañas viven en el contenido.
  if (d.querySelector(".site-header")) fail("sigue habiendo una barra de encabezado");
  const nav = d.querySelector(".u-nav");
  if (!nav) fail("sin navegación de pestañas");
  else {
    const cur = nav.querySelector('[aria-current="page"]');
    // El estado no puede quedar codificado sólo por el trazo (UMB-A11Y-005).
    cur ? ok(`pestaña actual «${cur.textContent}» de ${nav.querySelectorAll("a").length}`)
        : fail("ninguna pestaña lleva aria-current");
  }
  w.close();
}

/* ── 2. El buscador sigue buscando ─────────────────────────────────────── */
console.log("\n── búsqueda ──");
{
  const dom = new JSDOM(readFileSync(DIR + "index.html", "utf8"),
    {url: BASE + "index.html", runScripts: "outside-only", pretendToBeVisual: true});
  const w = dom.window;
  w.fetch = (u, o) => fetch(new URL(u, BASE).href, o);
  w.eval(readFileSync(DIR + "app.js", "utf8"));
  await new Promise((r) => setTimeout(r, 1500));
  const d = w.document;
  const q = d.getElementById("q");
  q.value = "carsol";
  q.dispatchEvent(new w.Event("input", {bubbles: true}));
  await new Promise((r) => setTimeout(r, 1200));
  // Se cuentan por contenedor, no en todo el documento: la página trae dos
  // búsquedas —órden del día y texto completo— y sumarlas daría un número que
  // no corresponde a ninguna de las dos.
  const agenda = d.querySelectorAll("#result-list li.result").length;
  const completo = d.querySelectorAll("#fulltext li.result").length;
  agenda === 2
    ? ok(`«carsol» → ${agenda} punto(s) del órden del día, ${completo} en texto completo`)
    : fail(`«carsol» daba 2 puntos del órden del día y ahora da ${agenda}`);
  d.querySelectorAll(".year-group").length ? ok(`línea de tiempo: ${d.querySelectorAll(".year-group").length} años`) : fail("la línea de tiempo no se dibujó");
  // La coincidencia no se codifica sólo por color (UMB-A11Y-005). Se lee la
  // REGLA: jsdom no resuelve font-weight de una hoja externa.
  const css = readFileSync(DIR + "styles.css", "utf8");
  const rule = (css.match(/\.result mark \{([^}]*)\}/) || [])[1] || "";
  (/font-weight:\s*600/.test(rule) && /text-decoration:\s*underline/.test(rule))
    ? ok("la coincidencia lleva peso y subrayado, no sólo color")
    : fail("la coincidencia quedaría codificada sólo por color");
  w.close();
}

/* ── 3. El panel construido, en instrumento ────────────────────────────── */
console.log("\n── panel (Observable Framework · instrumento) ──");
{
  const out = "site/panel/index.html";
  if (!existsSync(out)) {
    fail(`no existe ${out} — corre \`npm run build\` antes de verificar`);
  } else {
    const html = readFileSync(out, "utf8");
    // Los atributos tienen que viajar en el primer byte, no ponerlos el JS.
    /<html lang="es" data-mode="instrumento">/.test(html)
      ? ok('lang="es" y data-mode="instrumento" en el HTML construido')
      : fail("el <html> construido no trae lang y data-mode");
    // La paleta oscura tiene que estar en la hoja empaquetada.
    const href = (html.match(/\.\/_import\/umbral\.[a-f0-9]+\.css/) || [])[0];
    if (!href) fail("no se encontró la hoja empaquetada");
    else {
      const css = readFileSync("site/panel/" + href.slice(2), "utf8");
      css.includes("#101418") && css.includes("#edf1f4")
        ? ok("la hoja empaquetada trae la paleta instrumento")
        : fail("la hoja empaquetada no trae la paleta instrumento");
      /fonts\.googleapis|fonts\.gstatic/.test(css) && fail("la hoja carga fuentes de un CDN (UMB-TYP-005)");
    }
    /prefers-color-scheme/.test(html) && fail("el panel deja el modo al sistema del lector (UMB-COL-011)");
    // Las mismas medidas que las páginas estáticas.
    const sheetCss = readFileSync("site/panel/" + href.slice(2), "utf8");
    for (const [tok, esperado] of [["--u-sheet", "1200px"], ["--u-column", "1080px"], ["--u-edge", "32px"]]) {
      const got = (sheetCss.match(new RegExp(`${tok}:\\s*([^;]+)`)) || [])[1]?.trim();
      if (got !== esperado) fail(`el panel declara ${tok}: ${got ?? "—"}, el sitio usa ${esperado}`);
    }
    // La retícula del panel, comparada contra la del sitio declaración por
    // declaración: no basta con que las dos existan, tienen que pesar igual.
    // La retícula del panel contra la del sitio, declaración por declaración:
    // no basta con que las dos existan, tienen que pesar igual.
    const rp = reticula(sheetCss);
    const rs = reticula(readFileSync(DIR + "styles.css", "utf8"));
    const difs = ["opacity", "size", "image"].filter((k) => rp[k] !== rs[k]);
    difs.forEach((k) => fail(`la retícula difiere en ${k}: sitio "${rs[k] ?? "—"}" vs panel "${rp[k] ?? "—"}"`));
    if (!difs.length) ok(`retícula idéntica en las dos superficies (opacidad ${rp.opacity})`);
  }
  // La URL vieja sigue resolviendo.
  const redir = readFileSync(DIR + "panel.html", "utf8");
  /http-equiv="refresh"[^>]*\.\/panel\//.test(redir)
    ? ok("panel.html redirige a ./panel/")
    : fail("panel.html ya no redirige al panel");
}

console.log(bad ? `\n${bad} FALLA(S)` : "\n✓ todo conforme");
process.exit(bad ? 1 : 0);
