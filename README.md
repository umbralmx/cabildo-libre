# Actas Abiertas — Cabildo de Colima

Ventana pública y buscable a las decisiones del cabildo de Colima. El ayuntamiento
publica sus actas como un muro de PDF sin buscador; este proyecto convierte ese índice
en un sitio estático con búsqueda y línea de tiempo, enlazando siempre al documento
original.

**636 sesiones · 6,992 puntos de agenda · 2012–2026 · 5 administraciones.**

Un proyecto de **umbral_**. Código MIT. Proyecto independiente, sin relación con el
Ayuntamiento de Colima.

> **Estado (2026-07-22):**
> - **Fase 1 — en vivo** en <https://umbralmx.github.io/cabildo-libre/>: buscador y
>   línea de tiempo sobre el órden del día de las 636 sesiones.
> - **Fase 2 — en curso**, acotada al término actual (2024-2027, 74 actas): OCR del texto
>   completo + resúmenes en lenguaje llano con el *sentido* de cada punto. **23 de 74**
>   actas procesadas.
> - **X1 (legal) sigue abierto** — el sitio se lanzó en modo atribución con la revisión
>   de Términos y Condiciones aún pendiente. Ver
>   [`docs/x1-terminos-legal.md`](docs/x1-terminos-legal.md).
>
> Desarrollos, retos y próximos pasos: [`docs/bitacora.md`](docs/bitacora.md).

## Cómo funciona

```
SCRAPE ─▶ PROCESS ─▶ PUBLISH ─▶ SERVE
(GitHub Actions, por lotes)      (GitHub Pages, estático)
```

- `scraper/scrape_colima.py` — descarga el índice oficial y lo convierte en
  `data/actas.json`, `data/actas.csv` y sus copias para el sitio. Sólo biblioteca
  estándar de Python; sin dependencias. *(Fase 1)*
- `processor/` — pipeline de Fase 2: `ocr_colima.py` pasa por OCR los PDF escaneados del
  término (Tesseract `spa` sobre PyMuPDF) y `summarize_colima.py` redacta con DeepSeek un
  resumen y el *sentido* de cada punto. `build_site_index.py` compila los payloads del
  sitio. Ver [`processor/README.md`](processor/README.md).
- `site/` — sitio estático. La búsqueda y los filtros corren en el navegador sobre el
  JSON: no hay backend, base de datos ni índice del lado del servidor. La búsqueda cubre
  el órden del día y, en las actas ya procesadas, su texto completo.
- `.github/workflows/actualizar.yml` — re-scrapea lunes y jueves, commitea el dato si
  cambió y publica `site/` en GitHub Pages.
- `.github/workflows/procesar.yml` — corre el pipeline de Fase 2 por lotes (manual y los
  sábados): OCR, resúmenes y recompilación de los índices del sitio.

Restricción de diseño que explica lo anterior: **el mantenedor no puede operar ni pagar
un backend.** Todo debe ser estático y de nivel gratuito.

## Desarrollo local

```sh
python3 scraper/scrape_colima.py     # regenerar datos (descarga en vivo)
cd site && python3 -m http.server    # servir el sitio en localhost:8000
```

`--html copia.html` reparsea una copia guardada sin volver a descargar.

## Limitación central que conviene entender

La base del buscador es el **órden del día** de cada sesión —lo que estuvo en la mesa—,
disponible como texto en el índice oficial. Los PDF de las actas son escaneos sin capa de
texto, así que el *contenido íntegro* y el resultado de cada punto no salen del índice:
hay que hacer **OCR** (ver [`docs/a3-spike.md`](docs/a3-spike.md)). La Fase 2 los está
incorporando poco a poco, empezando por el término actual, y sobre ese texto un modelo
redacta resúmenes y el *sentido* de cada punto. Esos resúmenes son **generados por IA
sobre texto OCR y pueden contener errores**; cuando el acta no declara un resultado con
claridad se marca «sin resultado registrado» en vez de inventarlo, y el enlace lleva
siempre al documento original para verificar.

## Documentación

| Archivo | Contenido |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Contexto del proyecto, alcance, backlog y estado |
| [`docs/bitacora.md`](docs/bitacora.md) | **Bitácora de desarrollo:** qué se construyó, qué costó trabajo y qué sigue |
| [`docs/metodologia.md`](docs/metodologia.md) | Cómo se produce el dato: pipeline, reglas de parseo, decisiones editoriales, vacíos |
| [`docs/a3-spike.md`](docs/a3-spike.md) | Evidencia de que los PDF son escaneos y hace falta OCR |
| [`docs/phase2-ocr-spike.md`](docs/phase2-ocr-spike.md) | Spike de motor de Fase 2: Tesseract vs. visión, decisión DeepSeek y tabla de costes |
| [`processor/README.md`](processor/README.md) | Cómo corre la Fase 2: etapas de OCR y resumen, dependencias, reglas de honestidad |
| [`docs/x1-terminos-legal.md`](docs/x1-terminos-legal.md) | Hallazgos sobre los Términos y Condiciones, riesgo y opciones |
| [`docs/diseno.md`](docs/diseno.md) | Aplicación del sistema de marca Umbral y desviaciones deliberadas |
| [`data/SOURCE.md`](data/SOURCE.md) | Procedencia del conjunto de datos, caveats y licencias |

## Licencias

Código bajo **MIT**. La compilación y estructura de los datos, bajo **CC BY 4.0**. El
texto oficial de los órdenes del día es del Ayuntamiento de Colima, se atribuye y se
enlaza a su fuente; ver la posición completa —provisional, sujeta a X1— en
[`data/SOURCE.md`](data/SOURCE.md).
