# Actas Abiertas — Cabildo de Colima

Ventana pública y buscable a las decisiones del cabildo de Colima. El ayuntamiento
publica sus actas como un muro de PDF sin búsqueda; este proyecto convierte ese
índice en un sitio estático con buscador y línea de tiempo, enlazando siempre al
documento original.

Un proyecto de **umbral_** · datos CC BY 4.0 · código MIT.

## Cómo funciona

```
SCRAPE ─▶ PROCESS ─▶ PUBLISH ─▶ SERVE
(GitHub Actions, por lotes)      (GitHub Pages, estático)
```

- `scraper/scrape_colima.py` — descarga el índice oficial y lo convierte en
  `data/actas.json` (legible) y `site/actas.json` (minificado para el sitio).
  Solo biblioteca estándar de Python; sin dependencias.
- `site/` — sitio estático: búsqueda y filtros corren en el navegador sobre el
  JSON; no hay backend ni base de datos.
- `.github/workflows/actualizar.yml` — re-scrapea dos veces por semana, commitea
  los datos si cambiaron y publica `site/` en GitHub Pages.

## Desarrollo local

```sh
python3 scraper/scrape_colima.py     # regenerar datos (fetch en vivo)
cd site && python3 -m http.server    # servir el sitio en localhost:8000
```

## Estado

Fase 1 (índice buscable sobre los órdenes del día) — completa en local.
Fase 2 (texto completo de los PDF + resúmenes) requiere OCR: ver `docs/a3-spike.md`.
Contexto completo del proyecto en `CLAUDE.md`; procedencia de datos en `data/SOURCE.md`.
