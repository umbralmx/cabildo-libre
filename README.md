# Actas Abiertas — Cabildo de Colima

Ventana pública y buscable a las decisiones del cabildo de Colima. El ayuntamiento
publica sus actas como un muro de PDF sin buscador; este proyecto convierte ese índice
en un sitio estático con búsqueda y línea de tiempo, enlazando siempre al documento
original.

**636 sesiones · 6,992 puntos de agenda · 2012–2026 · 5 administraciones.**

Un proyecto de **umbral_**. Código MIT. Proyecto independiente, sin relación con el
Ayuntamiento de Colima.

> **Estado: Fase 1 construida y verificada en local; todavía no pública.**
> El lanzamiento depende de una revisión legal pendiente — ver
> [`docs/x1-terminos-legal.md`](docs/x1-terminos-legal.md). Léelo antes de publicar.

## Cómo funciona

```
SCRAPE ─▶ PROCESS ─▶ PUBLISH ─▶ SERVE
(GitHub Actions, por lotes)      (GitHub Pages, estático)
```

- `scraper/scrape_colima.py` — descarga el índice oficial y lo convierte en
  `data/actas.json`, `data/actas.csv` y sus copias para el sitio. Sólo biblioteca
  estándar de Python; sin dependencias.
- `site/` — sitio estático. La búsqueda y los filtros corren en el navegador sobre el
  JSON: no hay backend, base de datos ni índice del lado del servidor.
- `.github/workflows/actualizar.yml` — re-scrapea lunes y jueves, commitea el dato si
  cambió y publica `site/` en GitHub Pages.

Restricción de diseño que explica lo anterior: **el mantenedor no puede operar ni pagar
un backend.** Todo debe ser estático y de nivel gratuito.

## Desarrollo local

```sh
python3 scraper/scrape_colima.py     # regenerar datos (descarga en vivo)
cd site && python3 -m http.server    # servir el sitio en localhost:8000
```

`--html copia.html` reparsea una copia guardada sin volver a descargar.

## Limitación central que conviene entender

El texto buscable es el **órden del día** de cada sesión, no el contenido íntegro de las
actas: los PDF son escaneos sin capa de texto. Por eso el sitio muestra **lo que estuvo
en la mesa, no cómo se votó**, y por eso cada resultado enlaza al PDF original. Darle la
vuelta a esto es justamente la Fase 2, y exige OCR — ver
[`docs/a3-spike.md`](docs/a3-spike.md).

## Documentación

| Archivo | Contenido |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Contexto del proyecto, alcance, backlog y estado |
| [`docs/metodologia.md`](docs/metodologia.md) | Cómo se produce el dato: pipeline, reglas de parseo, decisiones editoriales, vacíos |
| [`docs/a3-spike.md`](docs/a3-spike.md) | Evidencia de que los PDF son escaneos y hace falta OCR |
| [`docs/x1-terminos-legal.md`](docs/x1-terminos-legal.md) | Hallazgos sobre los Términos y Condiciones, riesgo y opciones |
| [`docs/diseno.md`](docs/diseno.md) | Aplicación del sistema de marca Umbral y desviaciones deliberadas |
| [`data/SOURCE.md`](data/SOURCE.md) | Procedencia del conjunto de datos, caveats y licencias |

## Licencias

Código bajo **MIT**. La compilación y estructura de los datos, bajo **CC BY 4.0**. El
texto oficial de los órdenes del día es del Ayuntamiento de Colima, se atribuye y se
enlaza a su fuente; ver la posición completa —provisional, sujeta a X1— en
[`data/SOURCE.md`](data/SOURCE.md).
