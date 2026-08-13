# Bitácora de desarrollo — Actas Abiertas

> Registro cronológico de lo construido, lo que costó trabajo y lo que sigue.
> Complementa a `CLAUDE.md` (contexto y alcance) y a `docs/metodologia.md` (cómo se
> produce el dato). Entradas más recientes primero. Fechas absolutas.

---

## 2026-08-13 — El acta 48 no tenía un voto mal leído: tenía dos asuntos en un registro

**Tres decisiones del mantenedor, para no volver sobre ellas.** X1 legal: **adelante** — el sitio
sigue en modo atribución y lo que queda es postura, no permiso. `DEEPSEEK_API_KEY`: **ya está** en
los secretos del repo. Dominio: **`cabildo.umbral.org.mx`**, subdominio, para que `umbral.org.mx`
quede libre para el sitio principal. Y la Fase 3 queda **en pausa** hasta revisar el diccionario
de indicadores contra referencias externas.

**El término está completo y llevaba tiempo estándolo.** `CLAUDE.md` decía «76 de 78 actas», y
había 78 OCR, 78 resúmenes, actas 1 a 78 sin hueco, todas en `esquema 3`. **917 puntos**, 577
sustantivos (no-`tramite`) y de ésos 552 con resultado determinable; `no_determinable` en 2.7 %.
La cifra vieja venía de la entrada del 8 de agosto y nadie la volvió a mirar.

**El conflicto del acta 48 no necesitaba el PDF.** Estaba anotado desde el 26 de julio como «dos
ventanas que leyeron una decisión y la leyeron distinto», pendiente de cotejo manual. No era eso.
El 14 de octubre de 2025 la Síndica **retiró** del órden del día el dictamen de ampliaciones
SUPERNUMERARIO-BASE —el VII previo— y el Regidor Rangel **incorporó** otro asunto al final. El
cabildo aprobó la modificación por unanimidad y **todo lo posterior recorrió un lugar**: el VII
final son las tres licencias comerciales. El registro del punto 7 quedó con la prosa de un asunto
y los datos del otro: `sentido: aprobado`, `votacion: unanime` y `comision: Comercios, Mercados y
Restaurantes` son de las licencias, mientras el `resumen` habla del dictamen retirado. **La ficha
se delataba sola** — categoría `presupuesto_finanzas` con comisión de comercios— y las colonias
(Centro, Balcón de Abajo, Camino Real) son los tres domicilios de las licencias. Todo estaba en el
OCR; el cotejo manual nunca hizo falta.

**Y no era un caso: era una clase.** El órden del día que el resumidor entrega al modelo sale del
índice del portal, que publica el órden **previo** a la sesión. Cuando la sesión lo mueve, el
cuerpo del acta numera por el órden final y las ventanas discrepan: una obedece al índice, otra al
acta. `fusionar_puntos` une por `n` y funde dos asuntos. **Pasa en 19 de las 78 actas.** El acta 48
fue la única que gritó porque fue la única donde además discrepó el *sentido*; en las otras 18 el
desfase es silencioso. Peor: el acta 48 retiró uno e incorporó otro, así que **el órden previo y el
final miden lo mismo** y ningún conteo de longitud lo detecta.

**Dos señales independientes, mismas 19 actas.** `processor/orden_del_dia.py` ancla en la fórmula
de modificación («modificación al Orden del Día», «Orden del Día con la modificación», «con la
modificación autorizada») y contrasta con algo que no comparte ningún supuesto: cada impresión del
órden abre con «Lista de asistencia», así que el acta que lo modifica imprime la lista **tres**
veces y la que no, dos. Coinciden exactamente, sin falsos positivos ni negativos. **No se ancló en
«continuación»**, que era lo natural: el OCR la destruye una y otra vez —`CONtiINUACIÓN`,
`continua CIÓN`, y en el acta 47 directamente `CONAN`.

**Una petición de retiro puede perder.** En el acta 41 el cabildo aprobó retirar el Séptimo Punto
pero **no** aprobó retirar el Sexto. Dar por hecho que toda petición prospera habría movido puntos
que nunca se movieron, así que se transcribe la petición y, aparte, cómo se votó; el resultado sólo
se clasifica cuando el acta lo dice (17 unánimes, 1 parcial, 1 sin determinar).

**El arreglo va en el prompt, no en el JSON.** Misma doctrina que el acta 4/6 de julio: los
resúmenes se regeneran, así que corregirlos a mano es tinta perdida. Ahora la regla de numeración
es una sola para todas las ventanas —**manda el ordinal que el cuerpo del acta escribe**, no la
posición en la lista del índice— y, cuando hay modificación, el prompt lo advierte. **Los 19
resúmenes ya generados siguen mal**: repararlos es una corrida con `resumir_forzar`, ~$0.15, y es
decisión de costo del mantenedor.

**De paso, dos datos que no costaron nada.** `tipo_sesion` sale del encabezado en 76 de 78 actas;
las otras dos las salva el bloque de firmas, que declara el tipo otra vez y va anclado al número de
acta («las presentes firmas corresponden al Acta N° 54, de la Sesión Extraordinaria»). Con eso el
término queda en **42 extraordinarias, 32 ordinarias, 4 solemnes**, sin un solo `no_determinable`,
y sin adivinar: el acta 36 dice «Sesión **Grieco**» en el encabezado —OCR irrecuperable— y su firma
dice Ordinaria.

**Y un hallazgo que no buscábamos: cuatro actas se contradicen a sí mismas.** Las actas **2, 8, 40
y 59** declaran un tipo de sesión en el encabezado y el contrario en las firmas, con OCR limpio en
los dos lugares. No es ruido nuestro; es el registro público en desacuerdo consigo mismo, y el tipo
de sesión no es cosmético (ordinaria y extraordinaria tienen reglas distintas de convocatoria y
quórum). Se reporta, no se resuelve.

**Pendiente que queda anotado:** el asunto retirado se transcribe en 12 de las 19 actas y el punto
afectado se nombra por su ordinal en sólo 4; en el resto la petición existe pero el OCR no deja
leer el detalle. Se declara así, en hueco, como todo lo demás.

---

## 2026-07-26 — El término 2024-2027, completo: 74/74

**Cerrado.** Las 74 actas del término están OCR'd, resumidas y con asistencia: `74/74 con
resumen, 74 con Tier A, 74 con ficha, 74 con asistencia`. Se llegó en cuatro lotes desde 35,
sin una sola ventana fallida. **871 puntos**, de los cuales **545 son decisiones sustantivas**;
480 montos con cifra, 246 colonias mencionadas, 92 eventos de disenso o abstención, 81
comisiones, 222 contrapartes. Sólo **2 nombres quedaron sin mapear** al roster, y así se
declaran.

**El indicador que importaba se sostuvo.** `no_determinable` quedó en **22 de 871 (2.5 %)**
sobre el término entero. Venía de 2.3 % con 45 actas y 2.2 % con 65, mientras el corpus casi
se duplicaba: la lectura por ventanas del 25 generaliza a actas que no había visto cuando se
escribió, no estaba sobreajustada a las 25 de entonces. Para contexto, antes del arreglo era
58 %.

**Un solo conflicto en todo el término:** acta 48, punto 7 — dos ventanas que leyeron una
decisión y la leyeron distinto. Es exactamente la cola de revisión manual contra el PDF que la
lista debe producir; no se resolvió con un desempate silencioso.

**Los lotes no llegaban al sitio, y el arreglo del 25 no servía.** `procesar.yml` commitea con
el `GITHUB_TOKEN` y GitHub a propósito no dispara workflows con esos push. El gatillo
`workflow_run` que se le había puesto a `actualizar.yml` **nunca recibe el evento**: comprobado
dos veces, con el archivo asentado en main, los nombres idénticos byte por byte, ambos
workflows activos y la API reportando cero corridas con ese evento. En vez de seguir peleando
con la semántica, el lote **publica por su cuenta** (job `publicar` en `procesar.yml`, mismo
grupo de concurrencia `pages` para que los despliegues hagan cola). Los cuatro lotes de hoy
llegaron solos al sitio.

**Un lote ya no se pierde por un push rechazado.** El paso de commit hacía `git push` a secas;
basta con que algo entre a main durante la hora que dura un lote para que el push se rechace y
se tire el trabajo ya pagado. Ahora rebasa y reintenta. **No fue teoría: en el lote 56–65 el
push se rechazó de verdad** (`! [rejected] (fetch first)`), rebasó y entró al segundo intento.

**La sesión del 6/11/2024 es el acta 4, no un segundo acta 6.** El índice la rotula «006» pero
el PDF que ella misma enlaza es `acta-no-04.pdf`; la del 21 de noviembre —la otra que dice
«006»— enlaza `acta-no-06.pdf`. Un error de dedo en la fuente que producía dos anomalías: al
término le faltaba el acta 4 y el 6 estaba duplicado, con un id sintético (`2024-2027-6-2`) que
es lo que llavea todo aguas abajo. **No es inferencia**: el número sale de la fuente misma. Se
corrigió en el scraper —no a mano en el JSON, que se regenera en cada corrida— con el rótulo
original conservado en `no_acta_texto` y el número del índice en `no_acta_indice`. Se hizo
mientras el OCR aún no llegaba a las actas 4 ni 6, así que no costó reprocesar nada; un lote
más y habría sido retrabajo. Deliberadamente **no** se puso una regla general que prefiera el
enlace al texto —movería filas sin verificar—, pero sí una **detección** general: hoy reporta
un caso pendiente, el 30/09/2016, que el índice llama 52 y su enlace 51.

**Regenerar un resumen no reproduce el anterior**, y ya está escrito (`metodologia.md` §10.1).
Forzar la regeneración de las mismas 35 actas, con el mismo código y esquema, movió ~1 % de los
puntos en ambas direcciones — y `no_determinable` **subió** de 3 a 8. Es la dirección incómoda,
y por eso se declara: las cifras publicadas se mueven al refrescar el corpus aunque no entre
ninguna acta nueva. `--force` deja de ser rutina.

**Pendientes que quedaron anotados y no se tocaron:** el paso de commit de `actualizar.yml`
tiene el mismo `git push` a secas (su ventana es de segundos, no de una hora); cada corrida
commitea el campo `generado` aunque no cambie nada de fondo; y el acta 48 punto 7 sigue sin
cotejarse contra su PDF.

---

## 2026-07-25 — El corte de 45K era el defecto dominante, y el panel

**El hallazgo.** Al probar los 26 indicadores del diccionario contra los datos reales
(`docs/indicadores-revision.md`) apareció algo que no era un problema de indicadores sino de
tubería: **sólo el 25 % del texto OCR del término llegaba al modelo.** El tope de 45 000
caracteres en `summarize_colima.py` truncaba **17 de 25 actas** —la 64 tiene 553 K
caracteres, se leía el 8 %— y el resultado de un punto se asienta *al final* de su
discusión, justo en lo que se tiraba. La evidencia era limpia: 91 de 134 puntos sin
resultado en las actas truncadas, **0 de 24** en las ocho que cabían enteras.

**Nunca fue un problema de dinero.** Leer las 74 actas completas cuesta menos de un dólar.
Era que un acta de medio millón de caracteres no cabe en una llamada. La solución fue
leerla en **ventanas solapadas** (45 K, solape 3 K) y fusionar las fichas punto por punto.

**La regla que gobierna la fusión:** *un resultado asentado le gana a uno no leído.* La
ventana que no vio la votación devuelve `no_determinable`, y eso no puede pisar a la que sí
la vio. Si dos ventanas afirman resultados distintos gana la mayoría —empate, la posterior—
y el punto se reporta en `puntos_en_conflicto` en vez de resolverse en silencio. Las listas
se unen con dedup; nada se promedia. Si una ventana muere tras los reintentos se omite ella
sola y su hueco **se resta de la cobertura** en lugar de disimularse.

**El resultado, sobre las mismas 25 actas:**

| | antes | después |
|---|---:|---:|
| Puntos sin resultado legible | 91/158 (58 %) | **0/150 (0 %)** |
| Profundidad de lectura | 25 % | **100 %** |
| Actas leídas completas | 8/25 | **25/25** |
| Puntos con comisión · autor | 28 % · 37 % | **75 % · 83 %** |
| Montos con cifra · colonias | 52 · 57 | **129 · 100** |
| Eventos de disenso nombrados | 11 | **37** |

101 ventanas, ninguna fallida, ningún conflicto, ~$0.19. De paso se le pusieron reintentos
con backoff a `call_llm`: un lote anterior había muerto entero porque una sola respuesta de
DeepSeek llegó cortada.

**Un error de honestidad que ya estaba publicado.** El agregador sumaba el total de un
paquete de obra **junto con** su desglose obra por obra: en el acta 53 eso convertía
$661.8 M en $1,039 M. Ahora, cuando un monto iguala o supera a todos los demás del punto
juntos y el punto lista cinco o más, se toma sólo ese total; se publican también la suma sin
corregir y los puntos afectados, para que la corrección sea auditable y no un ajuste callado.

**El panel (L4).** `site/panel.html`, enlazado desde el buscador, con las ocho secciones que
los datos sostienen. Tres decisiones que valen registrarse (detalle en `docs/diseno.md`):
ninguna gráfica codifica por color —el gris y el signal de la marca se separan apenas ΔE 1.8
en deuteranopía, así que como pareja categórica no sirven—; los títulos se generan desde los
datos para que no queden desmentidos al crecer la cobertura; y cada gráfica tiene su gemela
en tabla con enlace al PDF, porque toda cifra tiene que poder verificarse contra el escaneo.

**Dos hallazgos sobre la fuente**, ambos del índice y no del OCR: al término le falta el
**acta 4**, y el **número 6 está asignado a dos sesiones distintas** (6 y 21 de noviembre de
2024). Se reportan tal cual; no se renumera nada.

---

## 2026-07-24 — L5: ficha de decisión con disidentes por nombre

**Hecho.** `summarize_colima.py` deja de dar un resumen genérico y produce una **ficha de
decisión** por punto (`esquema 3`): además de sentido/categoría/votación/colonias/obras/montos,
ahora extrae **`beneficiario` {nombre, tipo}** (a quién se dirige el recurso o el acto),
**`votos_en_contra`** y **`abstenciones`** como `[{nombre, id}]`, y **`comision`** + **`autor`**.
El `resumen` se reformuló a un takeaway concreto (qué, a quién, con cuánto).

**Disidentes por nombre, con honestidad.** El acta nombra a quién votó en contra; el modelo lo
devuelve como texto y `roster_match.py` lo mapea a un id del roster con la misma lógica tolerante
a OCR de la asistencia. Un nombre que no casa con nadie —un suplente, una errata— queda con
`id: null` y su nombre textual: **no se le atribuye el voto a un titular**. Probado con
"Fulano Inexistente" → `id: null`; Azucena/Diana → sus ids.

**Módulo compartido.** Se extrajo el emparejamiento de nombres a `roster_match.py`
(`build_index` + `emparejar`), reutilizable por el resumidor y, más adelante, por la asistencia.

**Pendiente de L5.** `reglamentos` y `obras_detalle` por punto; `tipo_sesion` por acta (parseo de
encabezado, sin LLM); enlace de `aplazados` en el agregador; y extender L3/L4 para consumir estos
campos. Luego, el pase enriquecido (re-OCR con `[ilegible]`/DPI + re-resumen) que los puebla.

---

## 2026-07-24 — Limpieza determinista del OCR (búsqueda + entrada al modelo)

**Hecho.** `processor/limpieza.py`: `limpiar()` quita la basura estructural del OCR crudo
—el membrete que se cuela en los saltos de página («ACTA DE CABILDO / DE COLIMA /
Administración 2024-2027»), corridas de guiones e iguales («----====--», «= = ="), bordes de
símbolos— y refluye párrafos. Integrada en `build_site_index.py` (los fragmentos de búsqueda
que ve el lector) y en `summarize_colima.py` (entrada al modelo: menos ruido, más contenido
real bajo el tope de 45k). Se regeneró `site/fulltext.json` (ahora arranca en «ACTA NUM. 1.-",
sin membrete).

**La línea que no se cruza.** La limpieza es **determinista**: no adivina ni reescribe
palabras. Un OCR mal leído («Orden del Diari» por «Día») se queda como está —corregirlo con un
modelo sería inventar registro público, justo lo que la regla del proyecto prohíbe—. El texto
crudo se conserva intacto en `data/ocr/` como evidencia; la limpieza se aplica al leer.

**Decisión de ruta (con el usuario).** Se descartó la idea de que un LLM «limpie» el OCR a
prosa fluida (fabricaría). El nivel elegido: **gratis + honesto**. Pendiente para el pase
enriquecido: marcar `[ilegible]` los tramos de baja confianza del propio Tesseract (necesita
re-OCR capturando confianza) y subir DPI/preprocesado; y reformular los resúmenes a
**fichas de decisión** (cuánto, a quién, y si hubo disenso) — converge con la épica L5.

---

## 2026-07-24 — Diccionario de indicadores + alcance del análisis

**Decisión de alcance.** Tras la nota de producto *El espacio de análisis* (~30 análisis posibles
sobre el corpus), se aprobó **avanzar con los niveles `ya` y `1 paso`** y dejar fuera los de nivel
*externo* (bloques de voto por partido, mapa geocodificado, colonias sin mención, búsqueda
semántica).

**Diccionario como fuente de verdad.** `data/indicadores.json` (máquina-legible) + `docs/indicadores.md`
(espec) enumeran **26 indicadores** —15 `ya`, 11 `1 paso`— agrupados por lente (dinero, decisiones,
personas, institución, geografía, confianza). Cada uno con pregunta, definición, fuente, cálculo,
audiencia y salvedad de honestidad. Es contra esto que se construyen el tablero (L4) y la extracción
pendiente (L5), no contra la memoria de una conversación.

**Corrección de un sub-alcance previo.** Antes marqué la "participación" como demasiado ruidosa para
ser honesta. El grep del corpus lo desmintió: las actas **nombran** a los disidentes ("votos en
contra de las Regidoras…", 15/25), a las comisiones que dictaminan (23/25) y a las empresas
contraparte (13/25). Todo eso está en el texto OCR; sólo falta estructurarlo — de ahí la épica **L5**.

**Backlog.** Se reencuadró L4 (primero los 15 `ya`) y se añadió L5 (extracción Tier A+ de un paso:
`empresas`, `votos_en_contra`, `abstenciones`, `comision`+`autor`, `reglamentos`, `obras_detalle`
por punto; `tipo_sesion` por acta; enlace de aplazados en el agregador). Próximos pasos: backfill
Tier A → L4 sobre los `ya` → L5 → extender L3/L4 para los `1 paso`.

---

## 2026-07-23 — L3: agregador de analítica por administración

**Hecho.** `processor/build_analytics.py` compila `site/analytics-2024-2027.json` a partir de
`data/summaries/` y `data/asistencia/`, integrado a `procesar.yml`. Secciones: cobertura,
decisiones (por sentido / categoría / votación), montos declarados, colonias y asistencia por
integrante (con suplencias y una fila por sesión).

**La honestidad va en la estructura, porque los agregados esconden sus propios huecos.**
Cada sección declara su base: el término tiene 74 actas, hay 25 con resumen y sólo **2** con
campos Tier A (categoría/votación/colonias/montos) hasta que corra el backfill `resumir_forzar`.
Los montos son `suma_declarada_mxn` con la nota de que **no** es el presupuesto del municipio,
sólo lo que las actas nombran. La tasa de asistencia excluye las sesiones `no_determinable`
(un mal escaneo no cuenta ni como presencia ni como falta): p. ej. Elia Moreno queda 18/23 =
0.783, sin castigarla por el acta 52 donde tuvo suplente. Los suplentes se listan, no se funden.

**Pendiente.** L4: la sección de gráficas en el sitio (dataviz + marca Umbral) con estas
salvedades a la vista, no enterradas. Y el backfill para engordar los agregados Tier A.

---

## 2026-07-23 — Cotejo contra PDF + detección de suplentes (no_reconocidos)

**Primera corrida real de DeepSeek.** Con la llave ya cargada, se corrió `procesar.yml`
(`lote: 2`) y se cotejaron las actas 52 y 53 contra el **PDF fuente** (verdad de origen, no
el OCR). Los campos Tier A salieron fiables: el monto del convenio CNEEG en el acta 53 es
**$661,792,051.55** exacto; `categoria: convenio`, `sentido: aprobado`, `votacion: mayoria`
—y el acta sí dice «aprobado por mayoría con los votos en contra de las Regidoras Azucena
López Legorreta y Diana Vizcaíno», así que la distinción unánime/mayoría es correcta—; las
colonias (Miguel Hidalgo, Fátima) son las dos únicas filas rotuladas «COLONIA» de una tabla
de 20, sin inventar colonias a partir de nombres de calle. Veredicto: **los resúmenes son
confiables, se puede escalar al término.**

**Hallazgo del cotejo: una suplencia.** El pase de lista del acta 52 nombra a **Nancy Susana
Martínez Briceño**, que no está en el roster, y **no** nombra a Elia Margarita Moreno (que
reaparece en el acta 53). Es una suplencia de una sesión. El extractor marcaba a la titular
como `no_determinable` y **descartaba en silencio** a la suplente.

**Arreglo (a): `no_reconocidos`.** El extractor ahora parsea los nombres del pase de lista
anclados en su título y reporta los que no casan con **ningún** integrante del roster —el
suplente— textualmente, sin forzarlo a un lugar del roster (regla de no inferir a quién
sustituye). Se resolvieron tres falsos positivos: cuando el OCR sólo deja los nombres de pila
(«Edgar Osiris», «Elia Margarita»), el reconocimiento ahora casa también por nombre de pila
(≥2 tokens), no sólo por apellido. Prueba: única acta marcada = 52 → «Nancy Susana Martínez
Briceño»; las otras 24, limpias. Salida `esquema: 2`. **Pendiente:** modelar la suplencia en
el propio roster (qué titular, qué sesiones).

---

## 2026-07-23 — L2: extractor de asistencia por sesión

**Hecho.** `processor/asistencia_colima.py` lee el pase de lista de cada acta y clasifica a
los 13 integrantes en `presente` / `remoto` / `falta_justificada` / `ausente` /
`no_determinable`, sin API (texto sobre el OCR). Corrió sobre las 23 actas: se ubican 12–13
de 13 en casi todas. Salida en `data/asistencia/`, integrada a `procesar.yml`.

**Dos trampas del OCR resueltas.** (1) Anclar en «Lista de asistencia» capturaba el *órden
del día* y colaba «licencia comercial» como si fuera un regidor con licencia; se ancló en
«manifestaron su presencia», que es el pase de lista real, no la agenda. (2) El OCR mutila
los apellidos (trunca «Legorret[a]», cambia «Aguirre»→«Aquitte»); emparejar el *par* de
apellidos fallaba. Se cambió a emparejar por el apellido **único** de cada integrante en el
roster, con tolerancia a truncamiento (prefijo) y a erratas (difflib) — así se ubica a Diana
por «Vizcaíno» sin depender del «Aguirre» que el escáner arruinó.

**La honestidad, otra vez en el borde.** En el acta 74 el acta sí nombra a Elia Margarita
Moreno en la asistencia remota, pero el OCR la deja como «ela mirar moro ar»: ilegible. Un
humano la deduciría por descarte; la regla del proyecto dice **no inferir**, así que queda
`no_determinable`, no `remoto`. Es el único `nd` de las 23. Las actas además distinguen
asistencia presencial, remota y falta justificada, y el extractor lo conserva.

---

## 2026-07-23 — L2: roster canónico del cabildo 2024-2027

**Hecho.** `data/regidores-2024-2027.json`: los 13 integrantes del cabildo (presidente,
síndica y 11 regidores), construidos a partir del **pase de lista de las propias actas**, no
de una fuente externa.

**El cruce importó.** El OCR del pase de lista del acta 1 traía dos nombres contaminados con
el apellido del regidor contiguo. Cruzando las actas 1/38/54/55 se corrigieron:
«Alondra Isabel Gallardo» → **López Alonso**; «Emilio Rosario Aldorica López Alonso» →
**Aldorica Pulido**; y se quitó una «H.» espuria de Edgar Osiris Alcaraz Saucedo. Se toma
como canónica la grafía que coincide en la mayoría de las actas, no la de una sola.

**Honestidad.** El roster es el cabildo *tal como se instaló*; no infiere sustituciones ni
licencias del período. Si el pase de lista de una sesión nombra a alguien fuera de la lista,
el extractor de asistencia (pendiente) debe marcarlo, no forzar la coincidencia. Cada
integrante lleva `variantes_ocr` para el mapeo de nombres ruidosos.

**Pendiente.** El extractor de asistencia por sesión que lea el pase de lista y lo cruce
contra este roster (marcando presente / ausente / remoto / falta justificada, que las actas
sí distinguen).

---

## 2026-07-23 — L1: esquema Tier A en el resumidor

**Hecho.** Se amplió el esquema por punto en `summarize_colima.py` para extraer, en la
misma llamada al modelo que ya se paga, los campos estructurados de la Fase 3 (Tier A):
`categoria` (vocabulario cerrado de 10), `votacion` (`unanime`/`mayoria`/`no_determinable`),
`colonias`, `obras` y `montos` (`{texto, valor_mxn}`). Salida marcada con `esquema: 2`.

**Honestidad, en el código y no sólo en el prompt.** `parse_summary` valida todo contra
vocabularios cerrados: categoría/sentido/votación inválidos caen a un valor seguro; las
listas mal formadas quedan vacías; y un `valor_mxn` que no sea número real se vuelve `null`
—nunca se coacciona un texto a número, para no fabricar una precisión que el acta no dio—.
Probado con entradas hostiles (categoría inventada, punto alucinado, monto = «mucho»): todo
se sanea. `build_site_index.py` no se toca (sólo lee `resumen`+`sentido`); los campos nuevos
son aditivos y el agregador (L3) leerá los `data/summaries/*.json` completos.

**Pendiente (necesita llave).** Re-generar las 23 actas ya resumidas para poblar el esquema:
`procesar.yml` con `resumir_forzar: true` y `lote ≥ 23`. Las 51 restantes ya salen con Tier A.

---

## 2026-07-23 — Nueva Fase 3: «The Lens» (analítica por administración)

**Decisión de alcance.** Se separó la antigua Fase 3 («Trends & Scale») en dos: la
**Fase 3 «The Lens»** —analítica por administración en una sección aparte— y la **Fase 4
«Scale»** —abstracción multi-municipio—. Motivo: la analítica es el trabajo de rendición
de cuentas #3 («seguir tendencias») y debe profundizarse sobre Colima *antes* de
generalizar a otras ciudades («Colima primero»).

**Qué medirá.** Por término: categoría del asunto (obra, licencia, fraccionamiento,
presupuesto, nombramiento…), sentido de la votación (unánime/mayoría), colonias y obras
*mencionadas*, montos *declarados explícitamente*, y **asistencia de regidores** (pase de
lista). Todo estático: JSON agregado por término, gráficas en el navegador (marca Umbral).

**El punto que sostiene la fase.** El resumidor de la Fase 2 ya lee el OCR completo y ya
toca categorías, colonias y montos, pero sólo como **prosa** dentro de `resumen`; nada es
consultable. La vía barata es **añadir campos estructurados al mismo esquema JSON de
`summarize_colima.py`** para que el dato analítico caiga del paso que ya se paga. **Van
23 de 74 actas.** Si se amplía el esquema *ahora*, las 51 restantes salen listas y sólo
se re-corren 23; si se termina el término primero, se re-corren las 74. → **Decisión
pendiente del mantenedor antes de seguir el lote de la Fase 2.**

**Honestidad.** Se conserva la regla del proyecto: nada de inferir vacíos. Montos y
colonias se muestran como *lo que el acta declara explícitamente*, con la salvedad visible;
«total discutido» = suma de montos nombrados, nunca un gran total sintético presentado como
autoridad. Participación a nivel de quién habló/propuso queda **fuera del v1** (demasiado
ruido para ser honesto). Épicas L1–L4 en `CLAUDE.md`.

---

## 2026-07-22 — Precisión de búsqueda y estado del término

**Hecho**

- **Búsqueda por frase exacta.** Entrecomillar la consulta —`"La Estancia"`— exige que
  las palabras aparezcan juntas y en ese orden. Sin comillas, la búsqueda sigue siendo
  por términos sueltos en cualquier orden.
- **Búsqueda consciente de palabras.** Antes, buscar `La Estancia` traía cualquier acta
  con «Las», «ला», etc., porque el término corto `la` casaba dentro de otras palabras.
  Ahora los términos de ≤3 caracteres exigen palabra completa (`\bla\b`) y los más
  largos permiten prefijo (`estancia`, `estancias`). Los fragmentos se anclan en el
  término más largo de la consulta, no en el primero.
- **Búsqueda en texto completo por defecto.** Ya no hace falta activar una casilla: al
  buscar, el sitio también rastrea el texto OCR de las actas ya procesadas y muestra
  **todas** las apariciones del término, con su contexto, declarando la cobertura
  («N coincidencias en R de T actas»).

**Estado del pipeline de Fase 2**

- **23 de 74** actas del término 2024-2027 con OCR + resumen. `fulltext.json` ≈ 4 MB.
- Coste DeepSeek observado: **~0.01–0.13 USD por lote**; muy por debajo del tope de 5 USD
  fijado por el mantenedor.

**Retos abiertos**

- **Sin pase visual del sitio.** Toda la integración de Fase 2 (resúmenes, sentido,
  panel OCR, búsqueda por frase) se verificó con un arnés headless de Node, no con un
  navegador real —la herramienta de navegador estuvo caída toda la sesión—. Falta que un
  humano vea la página en vivo, incluyendo móvil.
- **Escala de `fulltext.json`.** Se carga entero en el primer buscador. A 23 actas son
  ~4 MB; el término completo (74) rondará los ~12–13 MB. Conviene fragmentarlo (un
  archivo por acta + un índice compacto) **antes** de terminar el término, o la primera
  búsqueda se vuelve una descarga pesada en móvil.
- **Corte del OCR a 45 000 caracteres.** El resumen sólo ve los primeros 45k caracteres
  del acta. Basta para casi todas, pero actas muy largas (p. ej. acta 74, 108 pp.) se
  truncan y podrían perder resultados de las últimas páginas.

---

## 2026-07-20/21 — Integración de Fase 2 en el sitio

**Hecho**

- **Resúmenes en lenguaje llano bajo cada punto**, con etiqueta de *sentido* (aprobado,
  rechazado, aplazado, retirado, trámite, o «sin resultado registrado») y aviso claro de
  que son generados por IA sobre texto OCR.
- **Título de sesión como titular.** Cada acta encabeza con una frase que resume la
  sesión en conjunto, en vez del texto truncado del primer punto.
- **Vista de acta en el sitio.** Desde un resultado se puede abrir el resumen de la
  sesión y su texto OCR completo sin salir a descargar el PDF —aunque el enlace al
  documento original sigue presente para verificar.
- **Detalle de marca:** numeración de sección (`01 Datos`, `02 Metodología`) en mono.
- Payloads del sitio compilados por `processor/build_site_index.py`: `site/summaries.json`
  (pequeño, carga siempre) y `site/fulltext.json` (grande, carga perezosa).

**Retos resueltos en el camino**

- **Bug de fuentes en producción.** `fonts.css` resolvía a `assets/assets/fonts/…`
  (404) → las fuentes de marca no cargaban. Corregido a rutas relativas; verificado 200
  en vivo.
- **Python 3.7 local vs 3.11 en CI.** Las anotaciones `list[dict]` / `dict | None`
  fallan en 3.7.3 en tiempo de ejecución. Resuelto con `from __future__ import
  annotations` en los módulos del procesador.
- **Carrera de git con el bot de CI.** Empujar un commit mientras corría un lote hacía
  que el `git push` del bot fuera rechazado. Protocolo: commitear en local, esperar a que
  el lote termine, `git pull --rebase` sobre el commit de datos del bot y empujar.

---

## 2026-07-19/20 — Fase 2: decisión y pipeline

**Decisión de arquitectura.** OCR gratuito (Tesseract `spa` sobre PyMuPDF a 200 DPI) para
volver buscable el texto completo, y resúmenes con **DeepSeek** (`deepseek-v4-flash`,
texto solo, ~1 USD por término) para explicar cada punto. La llamada al modelo vive
aislada en `call_llm()` para poder cambiar de proveedor sin tocar el resto. Detalle y
tabla de costes en `docs/phase2-ocr-spike.md`.

**Regla de honestidad.** El OCR es ruidoso; el prompt ordena al modelo interpretar el
sentido a pesar del ruido pero **nunca inventar un resultado**: si el acta no lo declara
con claridad, el punto se marca `no_determinable`. Así se respeta la regla del proyecto
—*nunca rellenar un vacío de la fuente por inferencia*— aun con un resumidor de por medio.

**Spike A3 (invirtió el plan).** Se comprobó que **~100 %** de los PDF son escaneos sin
capa de texto (salida de escáner de oficina). La Fase 2 no era «sólo resúmenes»: cada
acta necesita OCR antes de cualquier resumen. Evidencia en `docs/a3-spike.md`.

---

## 2026-07-19 — Fase 1: índice buscable, sin abrir un PDF

**El hallazgo que lo hizo posible.** El órden del día de cada sesión ya está publicado como
**texto HTML** en el índice oficial, no encerrado en los PDF. Por eso la Fase 1 se
construyó sin abrir un solo documento: 636 sesiones y 6 992 puntos de agenda parseados del
índice, sin limpieza manual.

**Lo que costó trabajo (absorbido en el scraper).** Variantes de numeración, tres
grafías de «período» más una en blanco, cuatro estilos de numeración de agenda,
separadores de guiones, minutas derramadas en el texto, 4 sesiones duplicadas
(deduplicadas) y un salto de numeración en la propia fuente (acta 76/2017 va VI→VIII).
Reglas completas en `docs/metodologia.md` §3.

**Publicado.** Sitio estático en `umbralmx/cabildo-libre` → GitHub Pages, con re-scrapeo
programado. Búsqueda y filtros corren en el navegador; sin backend.

---

## Próximos pasos (propuestos, en orden de prioridad)

1. **X1 — legal.** Es el riesgo real, no una formalidad. Los Términos y Condiciones del
   portal prohíben la reproducción y comunicación pública de sus contenidos; el sitio ya
   está público en modo atribución. Movimiento barato y de alto valor: una solicitud
   formal de transparencia al Ayuntamiento y/o una consulta con R3D o Artículo 19 México.
   Decisión humana — ver `docs/x1-terminos-legal.md`. *(mantenedor)*
2. **Pase visual del sitio en vivo.** Nada se ha revisado con ojos en un navegador real;
   confirmar render y comportamiento, incluido móvil, antes de sumar funciones.
3. **Muestreo de calidad de los resúmenes.** Leer ~3–4 resúmenes contra su PDF para
   confirmar que el *sentido* es confiable **antes** de escalar a las 74 actas.
4. **Fragmentar `fulltext.json`** (un archivo por acta + índice compacto) antes de
   terminar el término, para no cargar ~12–13 MB de golpe.
5. **Terminar el término.** OCR + resumen de las 51 actas restantes, por lotes; revisar de
   paso el corte de 45k caracteres para actas muy largas.
6. **Más adelante:** los otros 4 términos (~560 actas), tableros de tendencias (Fase 3),
   dominio propio (X2) y anuncio de lanzamiento.
