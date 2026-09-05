/**
 * Cierra la construcción del panel: idioma y modo del documento.
 *
 * Todo lo demás (fuentes, logos, datos) viaja por FileAttachment, así que
 * Framework ya lo copia con su hash de contenido.
 *
 * Aquí NO se escribe un CNAME. El sitio se publica como project page de la
 * organización umbralmx, y una project page hereda el dominio de la
 * organization page. Un CNAME propio reclamaría el dominio entero para este
 * proyecto y tumbaría el sitio raíz.
 */
import {readdir, readFile, writeFile} from "node:fs/promises";
import {join} from "node:path";

const OUT = "site/panel";

/*
 * lang="es" (UMB-A11Y-001) y data-mode="instrumento" (UMB-COL-011).
 *
 * Framework emite <html> SIN atributo de idioma y no lo expone en la
 * configuración. No es un valor equivocado: es uno ausente, que es el caso
 * peor. Se reescribe el HTML ya construido para que los dos atributos viajen
 * en el primer byte y no dependan de que corra el JavaScript.
 *
 * `data-mode` conmuta los tokens a la paleta oscura. Si llegara por
 * JavaScript, la página parpadearía en claro antes de oscurecerse.
 */
const pages = (await readdir(OUT)).filter((f) => f.endsWith(".html"));
if (!pages.length) throw new Error(`${OUT}: no se construyó ninguna página`);

for (const page of pages) {
  const path = join(OUT, page);
  const html = await readFile(path, "utf-8");
  if (!html.includes("<html>")) {
    throw new Error(`${page}: no se encontró <html> sin atributos; ` +
      "revisa si Framework cambió la plantilla antes de confiar en este paso");
  }
  await writeFile(path, html.replace("<html>", '<html lang="es" data-mode="instrumento">'));
}

console.log(`lang="es" + data-mode="instrumento" en ${pages.length} página(s) de ${OUT}`);
