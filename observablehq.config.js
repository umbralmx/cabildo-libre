// Actas Abiertas · panel por administración — Observable Framework.
//
// **Modo instrumento (oscuro).** La tabla de superficies de la guía asigna
// `instrumento` al tablero, y `laboratorio` a la superficie web de lectura.
// Este proyecto tiene las dos y no son la misma cosa: el buscador y la
// metodología (site/) son documento y lectura, y siguen en laboratorio; este
// panel es un tablero sobre el término y va en instrumento (UMB-COL-011 — el
// modo lo fija el medio, no el `prefers-color-scheme` del lector).
//
// El panel se construye en `site/panel/`, de modo que el sitio estático que
// ya publica Pages lo absorbe sin cambiar cómo se despliega: se sigue subiendo
// `site/` entero.

const REPO = "https://github.com/umbralmx/cabildo-libre";

export default {
  title: "Panel por administración · Cabildo de Colima",
  root: "panel",
  output: "site/panel",

  // Hoja propia. Reemplaza al tema de Framework: la marca define color,
  // tipografía y mobiliario (UMB-COL-012 — un tema de Framework deriva cuatro
  // colores con color-mix() y ninguno llega a la compuerta de contraste).
  style: "umbral.css",

  // Framework carga Source Serif 4 desde Google Fonts si no se vacía esta
  // lista. Las fuentes se auto-hospedan (UMB-TYP-005).
  globalStylesheets: [],

  // Una sola página. La navegación de vuelta al buscador la pone chrome.js
  // dentro del contenido, no una banda fija.
  pages: [],
  sidebar: false,
  header: "",
  footer: "",
  pager: false,
  toc: false,
  search: false,

  head: `
<meta name="description" content="Qué decidió el cabildo de Colima en el término 2024-2027: asuntos, dinero declarado, asistencia de regidores y cadencia de sesiones, con la cobertura del análisis declarada.">
<link rel="icon" type="image/svg+xml" href="./assets/umbral-favicon.svg">`,

  interpreters: {".py": ["python3"]},
  preserveIndex: false,
  linkify: false
};
