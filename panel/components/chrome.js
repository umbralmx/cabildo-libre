/**
 * Marca, modo y vuelta al buscador.
 *
 * No hay barra de encabezado fija: la marca va al principio del contenido.
 * Una sola página no justifica una banda que repita lo que la página ya
 * muestra (guide/14-superficies/landing.md § Sin barra de navegación).
 */
import {FileAttachment} from "observablehq:stdlib";
import {html} from "npm:htl";

// El isotipo claro sobre fondo oscuro: el panel va en modo instrumento.
const isotipo = await FileAttachment("../assets/umbral-isotype-dark.svg").url();

/*
 * En el build, `scripts/copy-static.mjs` escribe estos dos atributos en el
 * HTML, que es lo que de verdad importa: llegan en el primer byte y no
 * dependen de que corra el JavaScript. Estas dos líneas dan la misma
 * corrección en `preview`, donde ese paso no se ejecuta.
 *
 * `lang` porque Framework emite <html> SIN atributo de idioma —no con uno
 * equivocado, con ninguno, que es el caso peor de UMB-A11Y-001—. `data-mode`
 * porque conmuta los tokens a la paleta oscura; si llegara por JavaScript la
 * página parpadearía en claro antes de oscurecerse.
 */
document.documentElement.lang = "es";
document.documentElement.dataset.mode = "instrumento";

/*
 * Los enlaces de vuelta son relativos. El panel se sirve en
 * `…/cabildo-libre/panel/` y el buscador un nivel arriba, así que `../`
 * resuelve igual en la raíz de un dominio que bajo un subcamino. Un enlace
 * absoluto saltaría al sitio raíz y sacaría al lector del proyecto.
 */
const PAGES = [
  {id: "index", href: "../", label: "buscador"},
  {id: "panel", href: "./", label: "panel por administración"},
  {id: "metodo", href: "../metodologia.html", label: "metodología"},
  {id: "fuente", href: "https://www.colima.gob.mx/portal2016/actas-de-cabildo/", label: "fuente oficial"}
];

/** El lockup, dentro del contenido. Vuelve al buscador. */
export function brand() {
  return html`<a class="u-brand" href="../" aria-label="umbral_ — inicio">
    <img src=${isotipo} alt="" width="24" height="24">
    <span class="u-wordmark">umbral<span>_</span></span>
  </a>`;
}

/** La navegación de vuelta. */
export function nav(current = "panel") {
  return html`<nav class="u-nav" aria-label="Secciones">
    ${PAGES.map(
      (p) => html`<a href=${p.href}
        aria-current=${p.id === current ? "page" : null}
        rel=${p.id === "fuente" ? "external" : null}>${p.label}</a>`
    )}
  </nav>`;
}

/** Etiqueta de sección: mono, minúsculas, en caption (UMB-LAY-006). */
export function label(text) {
  return html`<h2 class="u-label">${text}</h2>`;
}
