# A3 — Spike: extractabilidad de texto en los PDF de actas

**Fecha:** 2026-07-19 · **Muestra:** 8 actas distribuidas 2012–2026 (una por bienio)

## Resultado

**Las actas son escaneos de papel, no PDF de texto. Fase 2 requiere OCR en ~100% de los documentos.**

| Acta | Fecha | Descarga | Texto extraíble | Evidencia |
|---|---|---|---|---|
| 2012-2015 №6 | 2012-11-22 | **404** | — | ruta `portal2014` rota |
| 2012-2015 №76 | 2014-06-25 | **404** | — | ruta `portal2014` rota |
| 2015-2018 №42 | 2016-07-27 | ok (11 MB) | 0 caracteres | sin fuentes; página = 1 imagen |
| 2015-2018 №141 | 2018-08-14 | ok (68 MB) | 0 caracteres | productor: RICOH MP 305+ (escáner) |
| 2018-2021 №88 | 2020-06-24 | ok (2 MB) | 0 caracteres | productor: Scan Assistant |
| 2021-2024 №33 | 2022-07-13 | ok (34 MB) | 0 caracteres | productor: ScanPDFMaker + iLovePDF |
| 2021-2024 №119 | 2024-07-12 | ok (39 MB) | 0 caracteres | productor: Samsung K4350LX (escáner) |
| 2024-2027 №68 | 2026-03-11 | ok (20 MB) | 0 caracteres | sin fuentes; página = 1 imagen |

Método: `pypdf` — extracción de texto en 4 páginas por documento + inspección de
recursos de página (`/Font` vs `/XObject /Image`). Todas las páginas muestreadas
contienen una sola imagen y cero fuentes tipográficas.

## Implicaciones

1. **La hipótesis de CLAUDE.md era incorrecta.** Los sufijos `_opt` / `_compressed`
   indican compresión (iLovePDF), no texto digital. Los ayuntamientos imprimen,
   firman y escanean las actas.
2. **Fase 1 no se ve afectada** — la búsqueda se construye sobre el texto HTML del
   órden del día, que está completo en la página índice.
3. **Fase 2 necesita OCR.** Opciones a evaluar en su momento: Tesseract (spa) en
   GitHub Actions (gratis, lento, calidad media en escaneos con sellos/firmas) o
   un modelo de visión por lotes (costo único por acta, cacheado — el volumen
   razonable es acotar Fase 2 al período 2024-2027: ~75 actas).
4. **Enlaces rotos:** parte de los PDF 2013–2014 (rutas `portal2014`) devuelve 404
   (2 de 6 verificados por muestreo; el resto de patrones de URL responde 200).
   El sitio debe seguir enlazando — el enlace roto es del ayuntamiento, no nuestro —
   pero conviene un chequeo de enlaces periódico en Fase 2/3.
