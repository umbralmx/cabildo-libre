# Metodología — Actas Abiertas (Cabildo de Colima)

Cómo se produce el dato, qué decisiones se tomaron y dónde están los límites.
Última revisión: **2026-07-20**. Cifras de la corrida de esa fecha: **636 sesiones,
6,992 puntos de agenda, 2012–2026, 5 administraciones.**

Regla que gobierna todo el documento: **si no se puede reproducir con un script, no
se publica.** No hay ediciones manuales del dato en ningún punto de la cadena.

---

## 1. La cadena

```
SCRAPE ─────▶ PARSE ─────▶ PUBLISH ─────▶ SERVE
índice HTML   registros    JSON + CSV     sitio estático
oficial       estructurados en el repo    búsqueda en el navegador
```

- **Fuente única:** la página índice de
  [actas de cabildo del Ayuntamiento de Colima](https://www.colima.gob.mx/portal2016/actas-de-cabildo/).
  Un solo documento HTML (~2 MB) contiene las 640 filas de la tabla.
- **Procesamiento:** `scraper/scrape_colima.py`. Sólo biblioteca estándar de Python,
  sin dependencias, para que corra igual en una laptop y en GitHub Actions.
- **Salidas:** `data/actas.json` (legible, con indentación), `data/actas.csv` (formato
  largo) y sus copias en `site/` (JSON minificado) que consume el sitio.
- **Servicio:** todo el filtrado y la búsqueda ocurren en el navegador sobre el JSON.
  No hay backend, ni base de datos, ni índice de búsqueda del lado del servidor.

## 2. De dónde sale el texto buscable (y de dónde no)

**Dos niveles de información, y sólo tenemos el primero:**

| Nivel | Qué contiene | Dónde vive | ¿Lo tenemos? |
|---|---|---|---|
| **Órden del día** | Qué asuntos se pusieron sobre la mesa | Texto HTML en la página índice | **Sí** — es todo lo que indexamos |
| **Acta completa** | La discusión y el sentido de cada votación | PDF escaneado | **No** — requiere OCR (ver `a3-spike.md`) |

Consecuencia que hay que declarar siempre y no maquillar: **este sitio muestra lo que
estuvo en la agenda, no lo que se aprobó.** Un punto puede aparecer en el órden del día
y haberse retirado, votado en contra o modificado en la sesión. Por eso cada resultado
enlaza al PDF original: es la única forma de verificar el desenlace.

## 3. Cómo se parsea cada fila

Cada `<tr>` de la tabla da un registro con: `fecha`, `no_acta`, `periodo`,
`agenda_items[]` y `pdf_url`. El parseo tuvo que absorber varias irregularidades reales
de la fuente:

### 3.1 Fechas
Formato `13 mayo, 2026` → ISO `2026-05-13`. Una fila (acta 93, período 2018-2021) no
trae fecha en el índice: se conserva con `fecha: null` en vez de inventarla o
descartarla.

### 3.2 Números de acta
Aparecen como `074`, `0070`, `051` y una vez como `Acta 0003`. Se extrae el entero para
comparar y ordenar (`no_acta`) y se conserva la cadena original (`no_acta_texto`).

**Cuando el rótulo y el enlace de la misma fila se contradicen.** El índice rotula la
sesión del **6 de noviembre de 2024** como «006», pero el PDF que esa misma fila enlaza es
`acta-no-04.pdf`; la sesión del **21 de noviembre** también dice «006» y enlaza
`acta-no-06.pdf`. Es un solo error de dedo en la fuente que producía dos anomalías: al
término le faltaba el acta 4 y el número 6 aparecía dos veces.

Se corrige a `no_acta: 4`, y **no es una inferencia nuestra**: el número correcto sale de la
fuente misma —del archivo que la fila publica—, no de deducir qué número «debería» tocar.
El rótulo original se conserva en `no_acta_texto` (`"006"`) y el número que decía el índice
queda en `no_acta_indice` (`6`), así que la contradicción sigue siendo auditable en el dato
en vez de desaparecer. Con eso el término queda con la serie 1–74 completa y sin ids
sintéticos (antes esa sesión era `2024-2027-6-2`).

Las correcciones viven una por una en `CORRECCIONES_NO_ACTA`, en el scraper, con su
evidencia al lado. **Deliberadamente no hay una regla general** que prefiera el enlace sobre
el texto: movería filas que nadie ha verificado. Lo que sí es general es la *detección* — el
scraper compara cada rótulo con su enlace y **reporta** los desacuerdos en el resumen de
control sin tocarlos. Hoy queda uno así, sin verificar y por lo tanto sin corregir:

```
2016-09-30: el índice dice acta 52 pero su enlace es acta-0051.pdf — sin verificar, no se corrige
```

### 3.3 Períodos
Cinco administraciones escritas de formas inconsistentes: `2021 - 2024`, `2021-2024`,
`2018 -2021`. Se normalizan a `AAAA-AAAA`. Una fila viene con el período vacío y se
completa a partir de la fecha de sesión, sabiendo que los períodos municipales cambian
en octubre. Es la única inferencia de todo el pipeline, y queda documentada aquí.

### 3.4 División en puntos numerados — la parte delicada
El órden del día viene como un bloque de texto con guiones de relleno
(`-----------`) y numeración romana. Estilos encontrados en la fuente: `I.`, `I.-`,
`I` a principio de línea, y filas antiguas **sin numeral alguno**, separadas sólo por
corridas de guiones.

El parser busca numerales candidatos y **los valida contra la secuencia esperada**: el
primero debe ser I o II (una agenda arranca en II), y cada siguiente debe avanzar poco.
Esa validación es lo que evita falsos positivos como el tratamiento «C.» (C = 100 en
números romanos) o la V de «S.A. de C.V.».

**Tolerancia a saltos — hallazgo del 2026-07-20.** Exigir exactamente *anterior + 1*
resultó demasiado rígido: el acta 76 de 2017 salta de VI a VIII (error de numeración
del propio ayuntamiento). Con la regla estricta, el parser rechazaba todos los numerales
posteriores y **colapsaba cinco puntos distintos en uno solo**, que además quedaba
inflado y peor indexado. Ahora se admite un salto de hasta 3 posiciones: suficiente para
absorber un error de numeración de la fuente, y muy insuficiente para que se cuele un
«C.» (salto de ~90). Se respeta la numeración de la fuente tal como está — si el acta
salta de VI a VIII, el dato también.

Para las filas sin numerales existe un camino alterno: se parte por corridas largas de
guiones y se numera secuencialmente, dejando `numeral: null` para no fingir una
numeración que el original no tiene.

### 3.5 Texto derramado
Unas pocas celdas pegan, después del último punto («Clausura»), la minuta completa de
la sesión. Cuando eso ocurre se recorta en «Clausura» para que el último punto no quede
convertido en un muro de texto. El contenido íntegro no se pierde: está en el PDF, que
es la fuente citable.

### 3.6 Sesiones duplicadas
El índice lista 4 sesiones dos veces (misma fecha, mismo número, misma agenda),
a veces con un segundo enlace PDF equivocado que apunta a un acta distinta. Se conserva
un registro por sesión, prefiriendo el enlace cuyo nombre de archivo coincide con el
número de acta. Esto reduce de 640 filas a **636 sesiones**.

Ojo: **no toda coincidencia de fecha es un duplicado.** Hubo dos sesiones distintas el
14 de marzo de 2025 (actas 25 y 26) y ambas se conservan, como debe ser.

## 4. Búsqueda

- **Plegado de acentos y mayúsculas** carácter por carácter, preservando los índices
  del texto, de modo que las posiciones encontradas en el texto plegado se mapean 1:1
  sobre el original para resaltar la coincidencia exacta. «licencia» encuentra
  «Licencia»; «alcoholicas» encuentra «Alcohólicas».
- **Conjunción de términos:** un punto coincide si contiene *todos* los términos.
- **Unidad de resultado = el punto del órden del día**, no la sesión. Es lo que
  responde a la pregunta que motiva el proyecto («¿cuándo se aprobó lo de mi colonia?»).
- **Tope de 400 resultados** para no colgar el render; se avisa en pantalla cuando se
  alcanza en vez de truncar en silencio.
- **La búsqueda del órden del día** corre en memoria sobre ~7,000 puntos: a esa escala no
  hace falta índice, y evitarlo mantiene el sitio sin dependencias.

### 4.1 Búsqueda en el texto completo (Fase 2)

Buscar dentro del OCR es otro problema de escala: son ~11 millones de caracteres. Se
resuelve en dos etapas perezosas, ninguna con servidor.

1. **`site/fulltext-index.json`** (~1.0 MB) — índice invertido `token → actas`. Se descarga
   una sola vez, en la primera búsqueda de texto completo.
2. **`site/fulltext/<id>.json`** — el texto de **una** acta. Se pide sólo para las actas que
   el índice señala, y cada una se pide una sola vez por sesión.

**El índice acota, no decide.** Devuelve un superconjunto de candidatas —una consulta por
prefijo une los postings de todos los tokens que empiezan igual; una consulta de frase no
puede comprobar adyacencia— y sobre cada candidata corre **el mismo regex de siempre**. Por
eso los conteos, los fragmentos y el resaltado son idénticos a los del archivo monolítico
que esto sustituyó.

De ahí que el único fallo posible sea un **falso negativo**: un acta que coincide y que el
índice no propuso, lo que exige que falte un posting. `processor/verificar.py`
(`indice_completo`) vuelve a tokenizar cada acta en cada corrida y comprueba que todos sus
tokens apunten de vuelta a ella; si falla, la publicación se bloquea.

**Reproducirlo:** `python3 processor/build_site_index.py` regenera índice y textos desde
`data/ocr/`. Es determinista: mismo OCR, mismo índice.

**El costo que no baja.** Una frase entre comillas hecha de palabras comunes acota mal —
`"voto de calidad"` propone 65 actas y el regex se queda con 4—. Se midió un índice de
bigramas para arreglarlo (6.46 MB completo, 2.72 MB restringido a palabras comunes) y se
descartó por tamaño. El monolito anterior descargaba 10.9 MB en la primera búsqueda *siempre*;
aquí la primera búsqueda costó 1.46 MB medidos en el navegador, y sólo se acerca al tamaño
del corpus cuando la respuesta de verdad es «casi todas las actas».

## 5. Decisiones editoriales de presentación (y por qué son honestas)

Dos decisiones alteran cómo se *muestra* el texto, nunca el dato almacenado:

1. **Título corto de sesión.** Casi todos los puntos abren con la misma fórmula
   («Lectura, discusión y aprobación en su caso, del Dictamen que autoriza…»), lo que
   entierra el asunto real. En la línea de una sesión se recorta ese preámbulo para que
   se lea «Autoriza celebrar contratos de arrendamiento…». Si el recorte deja menos de
   12 caracteres, se descarta y se muestra el original. **El texto íntegro siempre está
   a un clic**, al desplegar la agenda, y en el JSON/CSV.
2. **Jerarquía de puntos procedimentales.** Lista de asistencia, quórum, lectura del
   acta anterior, receso y clausura se muestran en gris tenue para que los asuntos
   sustantivos lean primero. Es jerarquía visual, no filtrado: **ningún punto se oculta**
   y todos son igualmente buscables.

## 6. Vacíos conocidos — declarados, no imputados

| Vacío | Magnitud | Cómo se trata |
|---|---|---|
| Sesiones sin órden del día en el índice | 27 de 636 | Se conservan con agenda vacía y un mensaje explícito en pantalla |
| Sesión sin fecha publicada | 1 (acta 93, 2018-2021) | `fecha: null`; se agrupa por período |
| Enlaces PDF rotos en el servidor del ayuntamiento | Parte de 2013–2014 (rutas `portal2014`) | Se enlazan igual: la liga rota es del ayuntamiento y ocultarla sería borrar evidencia |
| Numeración saltada en la fuente | Al menos acta 76/2017 (VI→VIII) | Se respeta el salto tal cual |
| Contenido íntegro de las actas | 100% de los PDF | Fuera de alcance en Fase 1; requiere OCR |
| Estabilidad de los resúmenes entre corridas | ~1% de los puntos, en ambas direcciones | El modelo no es determinista; regenerar mueve las cifras. Medido y declarado en §10.1 |

Ninguno se rellena por interpolación ni se descarta en silencio.

## 7. Reproducir

```sh
python3 scraper/scrape_colima.py                    # descarga en vivo y regenera todo
python3 scraper/scrape_colima.py --html copia.html  # reparsea una copia guardada
cd site && python3 -m http.server                   # sirve el sitio en localhost:8000
```

El script imprime al terminar un resumen de control —registros, puntos, agendas vacías,
sesiones sin fecha, conteo por período y una lista de problemas detectados— que sirve
para comparar corridas y notar si la fuente cambió de forma.

## 8. Actualización automática

`.github/workflows/actualizar.yml` corre lunes y jueves: re-scrapea, commitea el dato
sólo si cambió y publica el sitio. Cada JSON lleva un campo `generado` con la marca de
tiempo de la corrida, que el sitio muestra como «Última actualización de los datos».

`procesar.yml` (los lotes de Fase 2, sábados) **publica al terminar su propio lote**, con un
job `publicar` propio. No delega en `actualizar.yml`: el lote commitea con el `GITHUB_TOKEN`
y GitHub a propósito no dispara workflows con esos push, y el gatillo `workflow_run` que se
intentó para despertarlo nunca recibió el evento (probado el 2026-07-25). Ambos despliegues
comparten el grupo de concurrencia `pages`, así que hacen cola en vez de pisarse.

## 9. Procedencia y licencias

Ver `data/SOURCE.md` y, importante, **`docs/x1-terminos-legal.md`**: los Términos y
Condiciones del portal contienen una cláusula que restringe la reproducción y
comunicación pública de sus contenidos. Eso está sin resolver y condiciona qué se puede
publicar y bajo qué licencia. El código es MIT; la estructura que aportamos se comparte
bajo CC BY 4.0; el texto oficial se atribuye a su fuente sin que nosotros pretendamos
licenciarlo.

## 10. Fase 2 — texto completo y resúmenes (en construcción)

Fase 1 indexa el **órden del día**. Fase 2 abre el **contenido de las actas** y le pone
resúmenes en lenguaje llano. Alcance inicial: el término **2024-2027** (74 actas). El
código vive en `processor/` y corre por lotes en GitHub Actions (`procesar.yml`), nunca
en el request. Detalle operativo en `processor/README.md`; la decisión de motores y su
costo en `docs/phase2-ocr-spike.md`.

Dos etapas, cada una cacheada: lo ya procesado se salta, así que reintentar un lote es
seguro y barato. Cacheada no es lo mismo que idempotente —volver a *generar* un resumen no
devuelve exactamente el anterior; ver §10.1.

1. **OCR — `ocr_colima.py` (Tesseract `spa`, gratis).** Los PDF son escaneos sin capa de
   texto (`a3-spike.md`), así que se rasteriza cada página a 200 DPI y se pasa por
   Tesseract. Salida: `data/ocr/<id>.json`, texto por página. Es un OCR **imperfecto**
   —numerales romanos mal leídos, caracteres sueltos, nombres propios aproximados— y así
   se declara; sirve para búsqueda de texto completo, que tolera ruido.
2. **Resúmenes — `summarize_colima.py` (DeepSeek, de pago, ~$1 el término).** Sobre el
   texto OCR, un modelo redacta por cada punto del órden del día un resumen llano y un
   `sentido` del acuerdo (`aprobado`, `rechazado`, `aplazado`, `retirado`, `tramite` o
   `no_determinable`). La llamada al modelo está aislada en `call_llm()` para poder
   cambiar de proveedor —o subir a un modelo de visión sobre las imágenes, si se quiere
   más calidad que la del texto OCR— sin tocar el resto del pipeline.

**La honestidad se mantiene con un summarizer de por medio.** El prompt obliga a
interpretar el sentido a pesar del ruido del OCR, pero prohíbe inventar: si el acta no
declara con claridad el resultado de un punto, queda `no_determinable`. La validación
descarta cualquier punto que el modelo devuelva y que no exista en el órden del día.
Cada resumen registra el `modelo` y la `fuente_texto` que lo produjeron.

**El acta se lee completa, por ventanas.** Durante un tiempo el paso de resúmenes enviaba
sólo los primeros 45,000 caracteres de cada acta, y eso truncaba 17 de 25: el desenlace de
un punto se asienta al final del punto, así que los que caían en páginas tardías quedaban
`no_determinable` no porque el acta callara, sino porque nadie había leído esa parte. Nunca
fue un problema de costo —leer el término entero cuesta menos de un dólar—, sino que un acta
de medio millón de caracteres no cabe en una llamada. Desde el 2026-07-25 cada acta se lee
en **ventanas solapadas** (45 K, solape 3 K) y las fichas se fusionan punto por punto, con
una regla explícita: **un resultado asentado le gana a uno no leído.** La ventana que no vio
la votación devuelve `no_determinable` y eso no puede pisar a la que sí la vio; `tramite`
cede igual, para que una ventana que sólo vio un punto de pasada no lo degrade. Si dos
ventanas afirman resultados distintos gana la mayoría —empate, la posterior— y el punto se
reporta en `puntos_en_conflicto` en vez de resolverse en silencio. Las listas se unen con
dedup; nada se promedia. Si una ventana muere tras los reintentos se omite ella sola y su
hueco **se resta de la cobertura** en lugar de disimularse.

**Contrapartida del proveedor elegido:** DeepSeek es sólo texto, por lo que resume sobre
el OCR ruidoso, más flojo justo en nombres de colonias y fraccionamientos —lo que la
gente busca. Se documenta como decisión consciente (`phase2-ocr-spike.md`) y es
reversible: subir a visión es cambiar tres variables de entorno.

### 10.1 Regenerar un resumen no reproduce el anterior

El caché hace que reintentar un lote sea seguro, pero **forzar la regeneración (`--force`) no
devuelve el mismo resultado**: el modelo no es determinista y sobre el mismo texto puede leer
un punto de otra manera. Medido el 2026-07-25 sobre las mismas 35 actas, con el mismo código
y el mismo esquema, la deriva fue de alrededor del 1 % y en las dos direcciones:

| | antes | después |
|---|---:|---:|
| Puntos detectados | 424 | 425 |
| `sentido: no_determinable` | 3 | **8** |
| Puntos con beneficiario | 128 | 134 |
| Categoría `tramite` | 215 | 210 |
| Eventos de disenso nombrados | 59 | 59 |

Dos consecuencias que conviene tener presentes al leer el panel:

- **Las cifras publicadas se mueven cuando se refresca el corpus**, aunque no entren actas
  nuevas ni cambie el código. No son un conteo estable del acta; son la lectura de un modelo,
  y se declaran como tal.
- **`no_determinable` puede subir**, no sólo bajar. En esa corrida pasó de 3 a 8. Es la
  dirección incómoda —el pipeline reconoció menos resultados que antes— y por eso se registra
  aquí en vez de dejar que parezca que la cobertura sólo mejora.

La lista `puntos_en_conflicto` también cambia entre corridas: en esa misma pasada desapareció
el conflicto del acta 51 (punto 18, que la regla de precedencia ya resuelve) y apareció uno
nuevo en el acta 48 (punto 7). Esa lista es justamente la cola de revisión manual contra el
PDF, no un defecto a ocultar.

Por eso el `--force` no se usa de rutina: sólo cuando cambia el esquema de extracción o una
regla de fusión, y el cambio vale la deriva.
