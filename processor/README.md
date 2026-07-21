# processor/ — Fase 2: OCR y resúmenes

Convierte los PDF escaneados de las actas en texto buscable (OCR) y en resúmenes
en lenguaje llano con el sentido de cada punto. Es la mitad **pesada y ocasional**
del proyecto: corre por lotes en GitHub Actions, no en cada visita. El resultado
—JSON en `data/ocr/` y `data/summaries/`— es lo que luego consume el sitio estático.

Alcance por defecto: **período 2024-2027** (74 actas), como acordado en `CLAUDE.md`.
Decisión de motores y costos: `docs/phase2-ocr-spike.md`.

## Las dos etapas

```
PDF escaneado ──▶ ocr_colima.py ──▶ data/ocr/<id>.json ──▶ summarize_colima.py ──▶ data/summaries/<id>.json
                  (Tesseract spa)     texto por página        (DeepSeek, texto)      resumen + sentido por punto
```

1. **`ocr_colima.py` — OCR (gratis).** Rasteriza cada página (PyMuPDF, 200 DPI) y la
   pasa por Tesseract `spa`. Es la única forma de sacar texto: las actas son escaneos
   sin capa de texto (`docs/a3-spike.md`). No se puede saltar con un modelo de texto.
2. **`summarize_colima.py` — resúmenes (DeepSeek).** Lee el texto OCR y, por cada punto
   del órden del día, pide un resumen llano y el `sentido` del acuerdo. La llamada al
   modelo está aislada en `call_llm()`: cambiar de proveedor (o subir a un modelo de
   visión) es editar esa función, no el pipeline.

## Dependencias

- **PyMuPDF** — `pip install -r processor/requirements.txt`
- **Tesseract + español** (binario del sistema):
  - Debian/Actions: `apt-get install -y tesseract-ocr tesseract-ocr-spa`
  - macOS: `brew install tesseract tesseract-lang`
- **`DEEPSEEK_API_KEY`** en el entorno para la etapa de resúmenes (secreto de Actions
  en CI). La etapa de OCR no necesita llave.

## Uso local

```sh
# OCR — cache-aware; --limit para procesar por lotes
python3 processor/ocr_colima.py --periodo 2024-2027 --limit 10
python3 processor/ocr_colima.py --id 2024-2027-1          # una sola acta

# Resúmenes — sobre lo ya OCR'd
export DEEPSEEK_API_KEY=sk-...
python3 processor/summarize_colima.py --limit 10
python3 processor/summarize_colima.py --id 2024-2027-1 --dry-run   # ver el prompt, sin gastar API
```

Ambas etapas son **idempotentes**: saltan lo ya hecho salvo `--force`. Por eso el
workflow puede ir llenando el corpus unas actas por corrida en vez de bajar 2 GB de
una sola vez.

## Cambiar de proveedor de resúmenes

`summarize_colima.py` lee tres variables de entorno (valores por defecto = DeepSeek):

| Variable | Default | Para qué |
|---|---|---|
| `LLM_ENDPOINT` | `https://api.deepseek.com/chat/completions` | endpoint compatible con OpenAI |
| `LLM_MODEL` | `deepseek-v4-flash` | modelo |
| `LLM_API_KEY_ENV` | `DEEPSEEK_API_KEY` | nombre de la variable que trae la llave |

Cualquier endpoint compatible con OpenAI (incluido un modelo de visión, si más adelante
se quiere calidad sobre imágenes en vez de texto OCR) funciona ajustando estas tres.

## Notas de calidad y honestidad

- El texto OCR es **ruidoso** (numerales romanos mal leídos, nombres imperfectos). El
  prompt obliga a interpretar el sentido sin inventar datos.
- **Nunca se inventa un resultado de votación.** Si el acta no lo dice con claridad, el
  punto queda como `sentido: no_determinable` —coherente con la regla del proyecto de
  no rellenar vacíos por inferencia.
- Cada resumen registra el `modelo` y la `fuente_texto` que lo produjeron, para poder
  auditarlo y regenerarlo.
