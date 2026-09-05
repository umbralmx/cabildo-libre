/**
 * Fuentes auto-hospedadas (UMB-TYP-005).
 *
 * Las @font-face se inyectan aquí y no en `umbral.css` porque el empaquetador
 * de CSS de Framework no tiene cargador para `.woff2`: una `url()` a una
 * fuente desde la hoja rompe la construcción. `FileAttachment` sí sirve
 * cualquier archivo y devuelve la misma URL con hash en `preview` y en
 * `build`. El precio es un cambio de fuente en la primera pintada, que cubren
 * `font-display: swap` y la pila de reserva de tokens.css.
 */
import {FileAttachment} from "observablehq:stdlib";

// Los dos subconjuntos que publica el proyecto. `latin` cubre el español
// salvo lo que cae en `latin-ext`.
const LATIN =
  "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, " +
  "U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, " +
  "U+FEFF, U+FFFD";
const LATIN_EXT =
  "U+0100-024F, U+0259, U+1E00-1EFF, U+2020, U+20A0-20AB, U+20AD-20CF, " +
  "U+2113, U+2C60-2C7F, U+A720-A7FF";

const FACES = [
  ["Space Grotesk", "500 600", FileAttachment("../assets/fonts/space-grotesk-latin.woff2"), LATIN],
  ["Space Grotesk", "500 600", FileAttachment("../assets/fonts/space-grotesk-latin-ext.woff2"), LATIN_EXT],
  ["IBM Plex Sans", "400 600", FileAttachment("../assets/fonts/ibm-plex-sans-latin.woff2"), LATIN],
  ["IBM Plex Sans", "400 600", FileAttachment("../assets/fonts/ibm-plex-sans-latin-ext.woff2"), LATIN_EXT],
  ["IBM Plex Mono", "400", FileAttachment("../assets/fonts/ibm-plex-mono-400-latin.woff2"), LATIN],
  ["IBM Plex Mono", "400", FileAttachment("../assets/fonts/ibm-plex-mono-400-latin-ext.woff2"), LATIN_EXT],
  ["IBM Plex Mono", "500", FileAttachment("../assets/fonts/ibm-plex-mono-500-latin.woff2"), LATIN],
  ["IBM Plex Mono", "500", FileAttachment("../assets/fonts/ibm-plex-mono-500-latin-ext.woff2"), LATIN_EXT]
];

const rules = await Promise.all(
  FACES.map(async ([family, weight, file, range]) => {
    const href = await file.url();
    return `@font-face{font-family:"${family}";font-weight:${weight};font-display:swap;` +
      `src:url("${href}") format("woff2");unicode-range:${range};}`;
  })
);

const style = document.createElement("style");
style.id = "umbral-fonts";
style.textContent = rules.join("\n");
document.head.append(style);

export const loaded = true;
