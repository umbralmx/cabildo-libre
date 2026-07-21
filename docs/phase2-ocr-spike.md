# Fase 2 — Spike de motor OCR (2024-2027)

**Fecha:** 2026-07-20 · **Alcance:** administración 2024-2027 (74 actas)
**Pregunta:** ¿qué motor OCR usar para volver buscable el contenido íntegro de las
actas y alimentar los resúmenes en lenguaje llano?

Precondición ya establecida (`docs/a3-spike.md`): los PDF son escaneos sin capa de
texto; el 100% requiere OCR.

## Muestra

Tres actas del término, en los tres casos difíciles, comparando **Tesseract 5.5
(`spa`)** contra **modelo de visión** sobre las mismas páginas rasterizadas a 200 DPI:

| Acta | Fecha | Págs | Caso duro probado |
|---|---|---|---|
| 2024-2027 №1 | 2024-10-16 | 5 | Encabezado con escudo + firmas en el margen |
| 2024-2027 №38 | 2025-06-30 | 64 | Anexo tabular (tabla de lotes de un fraccionamiento) |
| 2024-2027 №74 | 2026-05-13 | 108 | Página de firmas (cabildo completo firmando) |

## Resultado

| | Tesseract `spa` (gratis) | Modelo de visión (de pago) |
|---|---|---|
| Prosa impresa limpia | ~90% — buena, con ruido | Casi perfecta |
| Tabla de lotes (anexo) | ~90% — celdas ok, errores sueltos (`H4U`/`m4u`, `4`→`A`) | Perfecta, incluyendo códigos y calles |
| Página de firmas | **Pobre** — nombres rotos: «ALONDRA IL Z ALONSO», «AN ABEL» | Perfecta: nombres, cargos y pie legibles |
| Numerales romanos | Frágil: `I.`→`L`, `II.`→`Il.` | Correctos |
| Sangrado de firmas al texto | Se cuela como basura (`ÓN`, `———]`) | Ignorado correctamente |
| Costo | Cero. Corre en GitHub Actions (`apt install tesseract-ocr-spa`) | Costo único por página, cacheable |
| Ops | Cero | Requiere API key y presupuesto |

**Ejemplo, misma línea de la página de firmas del acta 74:**

- Original: `LICDA. ALONDRA ISABEL LÓPEZ ALONSO.`
- Tesseract: `LICDA. ALONDRA IL Z ALONSO.`
- Visión: `LICDA. ALONDRA ISABEL LÓPEZ ALONSO.`

Donde Tesseract más falla es justo en **nombres propios, colonias y fraccionamientos**
— exactamente lo que una persona busca. Y para los **resúmenes** (el diferenciador del
proyecto), alimentar texto ruidoso a un modelo degrada la calidad e introduce errores
en datos sensibles como direcciones.

## Volumen del término

- **74 actas · ~2.1 GB · ~6,000 páginas** estimadas.
- Distribución muy sesgada: la más grande pesa 182 MB; la mediana ~23 MB; la más chica
  1 MB. Buena parte de las páginas son **anexos tabulares repetitivos** (padrones de
  lotes), no prosa de decisión.
- Implicación de diseño: los **dictámenes** (lo que se decidió, la prosa) son una
  fracción de las 6,000 páginas. No hace falta transcribir con modelo de visión cada
  página de anexo para lograr el objetivo.

## Prioridades del proyecto que orientan la decisión

Según `CLAUDE.md`: (1) **encontrar** decisiones — la columna vertebral; (2) **explicar**
decisiones — el diferenciador. La primera se sirve bien con búsqueda de texto amplia
(tolera ruido); la segunda exige texto limpio en la prosa de decisión.

## Opciones

- **A — Sólo Tesseract (gratis).** OCR de las 74 actas en Actions; búsqueda de texto
  completo sobre todo. Cero costo, cero ops. Bueno para *encontrar*; flojo para
  *explicar* (resúmenes sobre texto ruidoso). No hay resúmenes de calidad.
- **B — Sólo visión (de pago).** OCR de todo con modelo de visión. Calidad casi
  perfecta, base ideal para resúmenes. Costo único proporcional a ~6,000 páginas
  (muchas son anexos que no aportan a la búsqueda ciudadana). Requiere API key.
- **C — Híbrido (recomendado).** Tesseract sobre todo el término para la **búsqueda de
  texto completo** (gratis, corre en Actions); modelo de visión **sólo sobre la prosa
  de dictámenes** para los **resúmenes en lenguaje llano + sentido del acuerdo**. Costo
  acotado a las páginas que importan, calidad donde importa. Encaja con las dos
  prioridades y con la restricción de «cero backend / cero ops» del servicio.

La decisión es del mantenedor porque **B y C implican gasto de API** (único y cacheado,
pero real) y una llave que no debo asumir.

## Decisión (2026-07-20): híbrido con DeepSeek para los resúmenes

Se eligió la **opción C (híbrido)** y, para el paso de resúmenes, el proveedor
**DeepSeek** en lugar de un modelo de visión de Anthropic.

- **OCR:** **Tesseract `spa`** sobre las 74 actas del término, gratis, en GitHub Actions.
  DeepSeek no puede hacer este paso: su API es **sólo de texto** (sin visión), y las
  actas son escaneos. El OCR *tiene* que hacerlo un motor que lea imágenes.
- **Resúmenes:** **DeepSeek** (`deepseek-v4-flash`, API compatible con OpenAI) sobre el
  texto que Tesseract extrae. La llamada al modelo queda **aislada** en
  `processor/summarize_colima.py` para poder cambiar de proveedor sin reescribir el
  pipeline.

### Costo estimado del término (una sola vez, cacheado en el repo)

Precios vigentes (2026-07): DeepSeek v4-flash $0.14/1M entrada, $0.28/1M salida;
Anthropic Haiku 4.5 $1/$5; Sonnet 5 $3/$15 (intro $2/$10); Opus 4.8 $5/$25. El OCR es
~6,000 páginas del término (~30M tokens de imagen si fuera por visión).

| Ruta | OCR / texto | Resúmenes | Costo aprox. | Calidad del resumen |
|---|---|---|---|---|
| **Tesseract + DeepSeek (elegida)** | Tesseract (gratis) | DeepSeek sobre texto | **~$1** | La más débil en nombres/colonias |
| Tesseract + Haiku (visión) | Tesseract (gratis) para buscar | Haiku lee las **imágenes** | ~$10–25 | Limpia |
| Visión en todo (opción B) | Haiku visión | Haiku visión | ~$33–66 (Batch: ~$33) | Limpia |

**Contrapartida asumida:** los resúmenes de DeepSeek se construyen sobre el texto
**ruidoso** de Tesseract, que es más flojo justo en nombres propios, colonias y
fraccionamientos —lo que la gente busca. Se mitiga de dos formas: la llamada al modelo
es intercambiable (se puede subir a visión después sin rehacer nada), y el prompt
obliga a marcar `sentido: no_determinable` cuando el desenlace no se lee con claridad,
en línea con la regla de **no rellenar vacíos por inferencia**.

## Reproducir

```sh
# rasterizar (pymupdf) y comparar motores sobre una página
python -c "import fitz; fitz.open('acta.pdf')[0].get_pixmap(dpi=200).save('p1.png')"
tesseract p1.png out -l spa      # motor gratuito
# el motor de visión se ejecuta contra la imagen p1.png vía API
```
