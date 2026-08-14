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
2. **`summarize_colima.py` — resúmenes (DeepSeek).** Lee el texto OCR (limpio) y, por cada
   punto, produce una **ficha de decisión** (`esquema 3`): resumen-takeaway, `sentido`,
   `categoria`, `votacion`, `colonias`, `obras`, `montos`, `beneficiario` (a quién),
   `votos_en_contra` / `abstenciones` (regidores, mapeados al roster con `roster_match.py`),
   `comision` y `autor`. La llamada al modelo está aislada en `call_llm()`: cambiar de
   proveedor (o subir a un modelo de visión) es editar esa función, no el pipeline.

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

## La puerta: `verificar.py`

Corre después de `build_analytics.py` y **antes de publicar**. Lee lo ya generado, no
llama a ningún modelo y termina en segundos.

```bash
python3 processor/verificar.py                        # comprueba
python3 processor/verificar.py --actualizar-linea-base # acepta cifras nuevas
```

Existe porque el proyecto declaraba bien su **procedencia** (cobertura, `no_determinable`,
nombres sin mapear) y no comprobaba el **significado**. Tres cosas se publicaron por esa
grieta: un monto de `$4,009,960,066` que el OCR del acta 17 nunca contuvo; 5 ventanas de
lectura fallidas que bajaron la cobertura a 98.09 % sin que nadie mirara; y un salto de
$13.2 a $17.1 mil millones en la suma declarada, sin umbral que lo detuviera.

| Comprobación | Severidad | Qué caza |
|---|---|---|
| `montos_en_fuente` | ERROR | Una cifra cuyo dígito a dígito no aparece en el OCR de su acta — es inventada |
| `lectura_completa` | ERROR | Actas resumidas con ventanas fallidas: texto que nadie leyó |
| `sin_conflictos` | ERROR | Puntos donde dos ventanas declararon resultados distintos |
| `cobertura_al_dia` | ERROR | El agregado quedó atrás de `actas.json` (el error de «74 sesiones») |
| `linea_base` | ERROR | Una cifra publicada se movió más de 3 % sin que nadie lo confirmara |
| `indice_completo` | ERROR | Al índice de búsqueda le falta un posting: habría consultas perdiendo resultados en silencio |
| `montos_no_aditivos` | AVISO | Un monto que iguala la suma de los demás — total+desglose que el guard de `build_analytics` no alcanza |
| `concentracion_del_dinero` | AVISO | Una sola categoría domina la suma, así que la suma no mide lo que su rótulo dice |
| `nombres_sin_mapear` | AVISO | Nombres que el acta cita y el roster no tiene — normalmente suplencias reales |

**ERROR bloquea la publicación, no el lote.** En `procesar.yml` la verificación corre antes
del commit (para que `data/linea-base.json` viaje en él) pero no detiene el job ahí: el lote
ya está pagado y queda commiteado e inspeccionable. Un paso final falla el job, y como
`publicar` depende de él, el sitio en vivo se queda con los datos anteriores.

La **línea base** (`data/linea-base.json`) no exige reproducibilidad exacta —re-resumir
mueve ~1 % de los puntos en ambas direcciones sin cambiar una línea de código— sino que
nadie mueva una cifra publicada más de un 3 % en silencio. Aceptar un cambio es explícito,
que es justo el momento en que alguien mira los números. No se ancla sobre una corrida con
errores: se crea en la primera corrida limpia.

## Notas de calidad y honestidad

- El texto OCR es **ruidoso** (numerales romanos mal leídos, nombres imperfectos). El
  prompt obliga a interpretar el sentido sin inventar datos.
- **Nunca se inventa un resultado de votación.** Si el acta no lo dice con claridad, el
  punto queda como `sentido: no_determinable` —coherente con la regla del proyecto de
  no rellenar vacíos por inferencia.
- Cada resumen registra el `modelo` y la `fuente_texto` que lo produjeron, para poder
  auditarlo y regenerarlo.
- **Capa de limpieza (`limpieza.py`), determinista.** Antes de mostrar el OCR en la
  búsqueda o de mandarlo al modelo se pasa por `limpiar()`: quita el membrete que se cuela
  en los saltos de página, corridas de guiones/iguales y refluye párrafos. **No corrige ni
  reescribe palabras** —un OCR mal leído se queda como está; reescribirlo sería inventar
  registro público. El texto crudo se conserva intacto en `data/ocr/` como evidencia; la
  limpieza se aplica al leer, no re-procesa.
- **Pendiente (pase enriquecido):** marcar como `[ilegible]` los tramos de baja confianza
  del propio Tesseract (requiere re-OCR capturando confianza) y subir DPI/preprocesado.
