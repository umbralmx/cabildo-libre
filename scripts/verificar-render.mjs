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
  const iso = d.querySelector(".brand img");
  if (iso && /isotype-light/.test(iso.getAttribute("src") ?? "")) fail("isotipo de fondo claro sobre fondo oscuro");
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
  }
  // La URL vieja sigue resolviendo.
  const redir = readFileSync(DIR + "panel.html", "utf8");
  /http-equiv="refresh"[^>]*\.\/panel\//.test(redir)
    ? ok("panel.html redirige a ./panel/")
    : fail("panel.html ya no redirige al panel");
}

console.log(bad ? `\n${bad} FALLA(S)` : "\n✓ todo conforme");
process.exit(bad ? 1 : 0);
