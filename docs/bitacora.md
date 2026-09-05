# Bitácora de desarrollo — Actas Abiertas

> Registro cronológico de lo construido, lo que costó trabajo y lo que sigue.
> Complementa a `CLAUDE.md` (contexto y alcance) y a `docs/metodologia.md` (cómo se
> produce el dato). Entradas más recientes primero. Fechas absolutas.

---

## 2026-09-05 — La costura que quedaba: dos anchos y dos encabezados

Con todo ya en modo instrumento quedaba una diferencia que se veía al navegar: el
panel y las páginas estáticas no compartían ni medidas ni encabezado. El buscador
tenía una columna de 880px con 24px de margen y una barra de encabezado; el panel,
hoja de 1200, columna de 1080, margen de 32 y la marca dentro del contenido. Pasar
de una página a la otra movía todo de sitio.

Ahora las dos usan las medidas de `desaparecidosmx`: `--u-sheet: 1200px`,
`--u-column: 1080px`, `--u-edge: 32px`. Y las dos usan el mismo encabezado: sin
barra, con la marca al principio del contenido y la navegación como pestañas
debajo.

Las pestañas son el control segmentado de UMB-LAY-008 —la regla de 1px del
contenedor es el riel y la actual se marca con un subrayado de 2px que se apoya en
él—. El subrayado va en `ink` y no en `signal`, porque la navegación no es capa de
dato y el acento tiene que quedar libre para la gráfica. La página actual lleva
`aria-current`, no sólo el trazo.

**La comprobación no es que las medidas valgan 1200/1080/32.** Es que valgan **lo
mismo en las dos superficies**: `verificar-render.mjs` lee los tokens de
`styles.css` y los del CSS empaquetado del panel y falla si se separan. Se probó
moviendo cada uno por su lado y las dos direcciones disparan.

**Un tropiezo, anotado porque es fácil repetirlo.** Al restaurar el árbol después
de esas pruebas usé `git checkout site/index.html` para deshacer una edición de
prueba. Pero el archivo tenía además el trabajo del día sin commitear, así que el
checkout lo revirtió entero al último commit y deshizo la reestructuración del
encabezado. Se detectó porque la suite volvió a fallar, no porque se notara. La
lección: para deshacer una edición de prueba sobre un archivo con trabajo sin
guardar, se restaura desde una copia hecha antes de la prueba, no desde git.

---

## 2026-09-05 — Un instrumento a medias claro no es un instrumento

**La corrección.** Se había movido sólo el panel a modo instrumento, apoyándose en
que la tabla de superficies pone `web` en laboratorio. El mantenedor lo corrigió:
**todas** las páginas de cabildo-libre van en instrumento. Tiene razón, y por una
razón que la tabla no alcanza a ver.

`cabildo-libre` no es un micrositio que habla de un proyecto: es la superficie de
consulta sobre el registro de actas de un ayuntamiento. En el vocabulario del
laboratorio es un **instrumento**. Es el mismo razonamiento con que
`desaparecidosmx` revirtió esta decisión el mismo día que la tomó: «la tabla de
superficies es la regla más específica, y esta página es un monitor sobre un
registro vivo, no una página sobre el proyecto.»

Y hay un argumento más fuerte todavía. Lo que UMB-COL-011 exige es **un solo modo
por artefacto**. Dejar el buscador en claro y el panel en oscuro producía media
superficie de cada color bajo el mismo dominio — exactamente el defecto que la
regla existe para evitar. La desviación no era poner todo en instrumento: era
haberlo partido en dos.

**Lo que costó.** Ni una regla de color. Los 63 usos de color de `styles.css` salen
de tokens, y `tokens.css` los redefine bajo `[data-mode="instrumento"]`. El cambio
completo es un atributo en el `<html>` de cada página, más el isotipo en su variante
`-dark` (la marca clara, `#5fd4c4`, para fondo oscuro). Es la primera vez que este
proyecto cobra lo que la cadena de tokens venía prometiendo.

**El atributo va en el HTML, no en el JavaScript**, o la página pinta en claro y se
oscurece a la vista del lector.

**Contraste: mejora.** 44 de 44 pares pasan en los dos modos, y en instrumento la
mayoría sube: `signal` sobre `base` pasa de 4.22:1 a 10.30:1.

**La puerta.** `verificar_marca.py` gana una comprobación que recorre página por
página: cada `site/*.html` declara instrumento, ninguna usa el isotipo claro, y
ninguna —ni la hoja— empareja un tema con `prefers-color-scheme`. La desviación
respecto de la tabla queda anotada en `docs/diseno.md`, no disimulada.

---

## 2026-09-05 — El panel era HTML a mano en modo claro, y debía ser un tablero

**El reclamo, y tenía razón.** Después de dar por terminada la migración de marca,
el mantenedor señaló dos cosas que no se habían hecho: los colores de modo
instrumento, y usar Observable Framework para el panel. Ninguna de las dos era una
omisión de detalle. Las dos estaban escritas en la guía y no se leyeron.

**Lo que dice la tabla de superficies.** Es explícita y no admite lectura:

| Superficie | Modo |
|---|---|
| Web | laboratorio |
| **Observable Framework — el tablero** | **instrumento** |

Y UMB-COL-011: «Laboratorio es lectura y documento. **Instrumento es tablero en
vivo.**» El panel es un tablero. Estaba en laboratorio, escrito a mano en HTML y JS,
mientras la guía movía la superficie de tablero a Framework desde la v1.4.0
(ADR-0004). Peor: `docs/diseno.md` afirmaba «no hay modo instrumento en este
proyecto», que era falso por no haber mirado la tabla.

**Qué se movió.** Sólo el panel. El buscador y la metodología no son tableros —son
lectura y documento— y se quedan en la superficie web, en laboratorio. La frontera
la fija la tabla, no la conveniencia.

El panel vive ahora en `panel/`, se construye a `site/panel/` y se sirve en
`…/cabildo-libre/panel/`. Las ocho gráficas se rehicieron en Observable Plot con el
tema del sistema. El encuadre lo valida `Frame` de `@umbralmx/umbral-plot`: se
**niega** a construir una gráfica sin fuente, y se comprobó que lanza.

**El modo vive en tres lugares y tienen que coincidir.** `MODE` en `format.js`,
`data-mode` en el `<html>` construido, y el isotipo claro sobre fondo oscuro. Si uno
se mueve solo, la página pinta medio clara o parpadea en claro antes de oscurecerse.
`verificar_marca.py` comprueba los tres, y las cinco comprobaciones nuevas se
probaron rompiéndolas una por una: **las cinco dispararon**.

**Las trampas de Framework no se volvieron a descubrir.** Están escritas en
`docs/framework-notes.md` de `desaparecidosmx` y se siguieron desde ahí: `style` y
nunca `theme` (un tema deriva colores con `color-mix()` que la compuerta de
contraste no puede medir); `globalStylesheets: []` o Framework trae fuentes de un
CDN; `<html>` sin `lang`, que es peor que uno equivocado; las `@font-face` por
`FileAttachment` porque el empaquetador no tiene cargador para `.woff2`; y el tope
de 640px que sólo se levanta para hijos directos de `#observablehq-main`, así que
toda gráfica dentro de una `<section>` se quedaba pequeña. Esa última es la que
cuesta ver: la gráfica se ve bien proporcionada, sólo que chica.

**Lo que no cambió.** Que ninguna gráfica codifique nada por color: `muted` y
`signal` no se separan bajo deuteranopía (ΔE 1.8), así que cada gráfica sigue siendo
de una sola serie y `signal` se sigue gastando en un único elemento, el medidor de
profundidad de lectura. Tampoco cambió el encuadre 2.0.0 ni la regla de no imputar.
Cambió el tiempo de ejecución debajo de esas decisiones, no las decisiones.

**Detalles de la migración.** El panel es salida de compilación y no se commitea:
vive en `.gitignore` y los dos jobs `publicar` lo construyen con Node antes de subir
`site/`. `site/panel.html` se quedó como redirección para que los enlaces viejos
sigan resolviendo. `@umbralmx/umbral-plot` no está en npm, así que se vendoriza en
`vendor/` como dependencia `file:`.

**Pendiente.** El repaso visual en pantalla, que sigue sin hacerse porque el
navegador continúa caído. Y el linter del sistema marca `panel/components/charts.js`
por no llevar línea de fuente: es un falso positivo que el propio `lint.py` explica
en su encabezado —la heurística mira un archivo a la vez— y aquí la garantía es más
fuerte, porque `chartFrame` se niega a construir sin fuente. Queda anotado con la
directiva `ignore-file` y documentado en `processor/README.md`.

---

## 2026-09-05 — El sitio llevaba un mes sin publicarse y nadie lo sabía

**El síntoma.** Al empujar la migración de marca, la corrida de despliegue se quedó en
`pending` sin arrancar ningún job. Al mirar el historial, **todas** las corridas desde el
2026-08-06 estaban en `cancelled`. Ni una sola publicación en un mes.

**Por qué no se notó.** Porque los datos sí llegaban. El job `procesar` terminaba en
`success` y commiteaba su lote —por eso hay cuatro commits «fase 2: procesar lote» en
agosto—, y sólo se moría el job `publicar`. El repo avanzaba y el sitio no. Un vistazo al
historial de commits no mostraba nada raro; había que mirar el estado **por job**:

```
procesar: completed/success
publicar: completed/cancelled
```

**La causa.** Una corrida programada del **2026-08-06** se quedó con su job `publicar` en
estado `waiting`, pidiendo aprobación del entorno `github-pages`. La petición no tenía
revisores y su temporizador era cero: nadie podía aprobarla nunca. Y como los dos workflows
comparten `concurrency: group: pages` con `cancel-in-progress: false`, esa corrida zombi se
quedó a la cabeza de la cola. Todo `publicar` posterior hizo fila detrás de ella y acabó
cancelado cuando entraba el siguiente. Las «duraciones» de 3 h y 41 h que mostraba el
historial no eran trabajo: era tiempo en cola.

`gh run cancel` no la mató —GitHub no cancela una corrida detenida en `waiting`—. La mató
`POST /actions/runs/{id}/force-cancel`. El despliegue pendiente pasó de `pending` a
`in_progress` en el instante en que se soltó el candado.

**El arreglo, para que no vuelva a pasar.** No basta con destrabarla a mano: hay que quitar
la posibilidad de que una corrida atascada bloquee a las demás.

- Los dos jobs `publicar` pasan a `cancel-in-progress: true`. De un despliegue sólo importa
  el último, así que uno nuevo **reemplaza** al anterior en vez de hacer cola detrás de él.
  Una corrida zombi ya no bloquea: la siguiente la sustituye.
- En `actualizar.yml` el grupo `pages` estaba a nivel de **workflow**, así que cubría también
  al re-scrapeo. Se movió al job `publicar`, y el workflow queda en un grupo `actualizar`
  propio con `cancel-in-progress: false`: el scrape escribe en git y no debe cancelarse a
  media escritura.
- El grupo `procesar` sigue en `false`. Ese job cuesta dinero y hasta 330 minutos; un
  despliegue no lo cancela.

**Queda pendiente.** Las cuatro acciones (`checkout@v4`, `configure-pages@v5`,
`deploy-pages@v4`, `upload-artifact@v4`) apuntan a Node 20 y el runner las fuerza a Node 24.
Funciona, y conviene subirlas antes de que deje de funcionar.

---

## 2026-09-04 — El sistema de marca llegó a 2.0.0 y el sitio se quedó en 1.1.0

**Qué cambió afuera.** `umbral-style-guide` avanzó cuatro versiones desde que este sitio
se diseñó. Tres importan aquí:

- **1.2.0** hizo normativo el *idioma mínimo*: etiquetas de sección en mono y **minúsculas**,
  listas separadas por reglas de 1px **en vez de tarjetas**, controles secundarios en mono
  con borde de 1px, y la retícula de puntos acotada al margen exterior.
- **1.6.0** publicó `components.css`, la hoja **escrita a mano** con los diez componentes
  que necesita una superficie de datos. Es la única hoja del sistema que edita una persona.
- **2.0.0** rompió el marco de gráfica, y nombra a `cabildo-libre` en su lista de migración.

**Lo que rompió 2.0.0.** El subtítulo ya no es `geografía · periodo · unidad`: dice **cómo
está construida** la cifra —la transformación, la unidad, el alcance y el periodo—. La razón
es concreta: una suma acumulada y un total anual dibujan curvas distintas con los mismos
datos, y el subtítulo viejo no nombraba ninguna de las dos. Y la línea de fuente pasó a tener
**dos lados**: origen y fecha de consulta a la izquierda, el sitio a la derecha. La licencia
y la etiqueta de instantánea se **mudaron a la página**, porque cinco campos en una línea no
sobrevivían a una tarjeta social ni a una diapositiva.

Las ocho gráficas del panel llevaban la línea vieja. Ahora las ocho leen, por ejemplo:

```
Fuente: Elaboración propia con el pase de lista de cada acta de cabildo del
Ayuntamiento de Colima. Consulta realizada el 2026-08-14.        umbral.org.mx
```

La fecha se lee de `generado` en el payload, nunca escrita a mano: es la misma disciplina
que ya rige a la página de metodología.

**Lo que se adoptó.** El sitio ahora carga `components.css` y **borra su copia local** de
cada forma que la hoja ya define. Los controles, la tabla gemela, el buscador de colonias,
la fila de KPI y los renglones de resultado dejaron de tener CSS propio. Son ~110 líneas
menos y, sobre todo, un solo lugar donde vive cada forma. Dos consecuencias visibles: los
KPI pasan a **mono tabular** —se leen columna contra columna, y para eso sirve la cifra
mono— y los resultados de búsqueda dejaron de ser **tarjetas**: hoy son renglones separados
por reglas de 1px, como manda UMB-LAY-007.

**Dos hallazgos que no se buscaban.**

1. `assets/tokens.css` —la carpeta fuente de marca— seguía en la **versión 1.0**, con
   `caption` en `#9AA19B`: **2.37:1**, el peor fallo de contraste que midió la auditoría de
   julio. El sitio servía la copia corregida, así que nadie lo veía. Las dos copias no se
   comparaban con nada. Ahora sí.
2. La gráfica de cadencia decía en su título «sesionó **78** veces» y en su subtítulo
   «cubre las **74** sesiones del término». El 74 estaba escrito a mano y se quedó ahí
   cuando el término creció. Es exactamente la falla contra la que advierte el encabezado
   de `metodologia.js`. Las dos cifras se leen del payload.

**Una separación que faltaba.** La página de metodología tenía cuatro bloques con el marco
de gráfica y sólo **uno** era una gráfica. Los otros tres son un encabezado, un párrafo y
una tabla de referencia. Llevar el marco los obligaba a UMB-CHT-002 y UMB-CHT-003, que no
podían cumplir con honestidad: una tabla que describe **nuestro propio proceso** no tiene
fuente externa, y poner al Ayuntamiento como origen le atribuiría una afirmación que nunca
hizo. Se separaron: `.fig` significa *figura sobre datos*, `.explica` es prosa con la misma
tipografía y sin la promesa.

**La puerta.** `processor/verificar_marca.py` — 165 líneas, sin dependencias, sin navegador.
El linter del propio sistema ya pasaba limpio: la capa mecánica (hexes, radios, sombras) no
era el problema. Lo que no puede ver es el contrato del marco, que vive en la prosa y en el
JS que la genera. La puerta revisa los dos lados de la línea de fuente, que el subtítulo
nombre una transformación y un periodo, el dominio, las versalitas, la licencia en la página
y la **deriva de tokens** contra el repo de la guía. Las seis comprobaciones se probaron
rompiendo el sitio a propósito una por una: **las seis dispararon**.

Se verificó también con render real (jsdom): las tres páginas montan sin errores, la búsqueda
de «carsol» sigue dando sus dos puntos y la línea de tiempo sus 15 años. **El navegador
seguía caído**, así que falta el repaso visual — igual que el 2026-07-20. Vale la nota de
`docs/framework-notes.md` de desaparecidosmx: durante aquella migración el navegador devolvió
marcos obsoletos dos veces y llevó a concluir que una página que funcionaba estaba congelada.
Aquí jsdom hizo lo mismo en pequeño —devolvió estilo vacío para reglas que sí existen— y por
eso la puerta lee la regla CSS, no el estilo computado.

**Sigue pendiente.** El repaso visual en pantalla. Y la retícula de puntos es la única pieza
del idioma mínimo que se añadió sin haber estado antes: si estorba, se quita borrando un
bloque de `styles.css`.

---

## 2026-08-14 — El sistema declaraba de dónde venía cada cifra, no si era cierta

**El diagnóstico.** Se revisó el plan completo contra los tres objetivos de `CLAUDE.md`.
El hallazgo no fue que faltara análisis: fue que la arquitectura de honestidad —buena, y
mejor que la de casi cualquier proyecto de datos cívicos— vigila la **procedencia** y es
ciega al **significado**. Cada sección declara su `cobertura`, `no_determinable` es un valor
y no un cero silencioso, los nombres que no casan se reportan en vez de forzarse. Nada
preguntaba nunca *si una cifra quiere decir lo que dice su etiqueta*.

Los $17.1 mil millones del panel pasan **todas** las comprobaciones que el proyecto tenía:
son la suma de cantidades enunciadas explícitamente, con su base declarada, con una nota
que aclara que no es el presupuesto, y con el guard de doble conteo revelado en pantalla. Y
suman ingreso ($937M) + gasto ($971M) + la diferencia entre ambos ($34M), que es el acta 17
punto 7 leyendo un informe de cuenta pública. El 91.4 % del total sale de
`presupuesto_finanzas`, que son en su mayoría informes, no dinero que el cabildo aprobó.

El caso más claro: el acta 17 declaró durante semanas **$4,009,960,066**. El OCR contiene
`1,009,960,065.66` seis veces y `4,009,960,066` **cero**. Una cifra inventada, con
procedencia impecable. El re-resumen del 2026-08-14 la corrigió sola, y nadie se habría
enterado de que existió.

**Lo construido: `processor/verificar.py`.** Ocho comprobaciones, ninguna llama a un modelo,
todas corren en segundos sobre lo ya generado. Cinco son ERROR y bloquean la publicación;
tres son AVISO porque piden criterio, no corrección. Tabla completa en `processor/README.md`.

**Lo que encontró en su primera corrida**, todo en vivo:

- **2 de 785 montos** citan una cifra que su acta no contiene —acta 53 p6 (`$53,075,182.12`)
  y acta 60 p5 (`$1,302,340.27`)—, y no aparecen ni tolerando los separadores rotos del
  escáner. Son construidas.
- **4 actas con ventanas fallidas** (34, 46, 51, 76 — 5 ventanas): texto que no se leyó.
- **6 puntos** donde un monto iguala la suma de los demás. `_suma_punto` sólo actúa con
  cinco montos o más, así que el caso de tres —el del acta 17— se le escapaba entero.
- El **91.4 %** de concentración del dinero en una categoría.

**La línea base es la pieza que faltaba el 2026-08-14.** El re-resumen movió la suma
declarada de $13.2 a $17.1 mil millones (+29.4 %) y nada dijo nada. Ahora `data/linea-base.json`
guarda 13 cifras publicadas y cualquier movimiento de más del **3 %** falla la corrida hasta
que alguien lo confirme con `--actualizar-linea-base`. El umbral está calibrado sobre el
ruido real: en la misma corrida `n_puntos` se movió −0.87 % y, correctamente, no se quejó.
No se ancla sobre una corrida con errores; se creará en la primera limpia.

**Dónde va la puerta.** En `procesar.yml` corre *antes* del commit —para que la línea base
viaje en él— pero con `continue-on-error`: el lote ya está pagado y tiene que quedar en el
repo. Un paso final falla el job, y como `publicar` depende de él, el sitio en vivo se queda
con los datos anteriores en vez de estrenar números que nadie revisó.

**Lo que esto reordena.** Desde el 2026-07-23 el trabajo fue casi todo Fase 3, que
`CLAUDE.md` marca como *deferred*, mientras el objetivo 1 (la búsqueda, «la espina dorsal»)
arrastra desde el 2026-07-20 su único defecto conocido —`fulltext.json`, 10.9 MB que se
cargan enteros en la primera búsqueda— y el objetivo 2 (los resúmenes, «el diferenciador»)
nunca se muestreó contra un PDF, pese a proponerse el 2026-07-20 *antes* de escalar. Fase 3
sí encontró defectos reales (la ventana de 45K, el acta 48), pero es un detector caro:
publica el error y después lo nota.

**Siguiente, en orden:** (1) re-correr las 4 actas con ventanas fallidas; (2) decidir qué
hace el panel con la suma de dinero —acotarla a categorías de aprobación o retirarla, que es
decisión editorial; (3) el índice invertido de búsqueda (medido: 1.03 MB contra 10.9 MB, 10×,
con la misma semántica); (4) el muestreo de resúmenes contra PDF; (5) y sólo entonces Fase 3,
por R1/R2/T4/I3, que no cuestan nada porque `data/estructura/` ya los tiene.

---

## 2026-08-13 — Una metodología pública, y dos cifras que se estaban contando mal

**Qué se agregó.** `site/metodologia.html` + `metodologia.js`: la explicación del método para
quien no va a abrir `docs/metodologia.md` —organizaciones, prensa, servidores públicos—. Ocho
secciones: por qué el problema es de navegación y no de secreto, el recorrido de un acta en cinco
etapas, la regla de honestidad, los tres problemas que costaron trabajo (escaneos sin texto, la
ventana de 45K, la renumeración del órden del día), qué se puede medir y qué no, el fundamento en
el artículo 34 de la Ley de Transparencia de Colima, los límites conocidos y la reproducibilidad.
Enlazada desde el buscador y desde el panel; las secciones cortas de metodología que ya vivían en
esas dos páginas se quedan donde estaban y ahora apuntan a la página larga.

**Ninguna cifra de la página está escrita a mano.** Salen de `analytics-<termino>.json` y
`actas.json` por una razón concreta: el panel estuvo publicando «74 sesiones» semanas después de
que el término creciera a 78, porque el número estaba en prosa. Los marcadores del HTML traen un
valor de respaldo para que la página se lea sin JavaScript, y el JS los sustituye si el dato carga.
Para lo que faltaba se extendió `build_analytics.py` con una sección `estructura` que agrega lo que
`orden_del_dia.py` ya leía del acta: tipo de sesión (42 extraordinarias, 32 ordinarias, 4 solemnes),
19 actas que modifican su órden del día, 12 con el asunto legible, 4 que se contradicen a sí mismas.

**El pase visual encontró dos defectos, y uno era de honestidad.** La página publicaba **2.7 %**
de decisiones «sin resultado legible». La cifra correcta es **4.3 %**: `por_sentido` sólo clasifica
los puntos **sustantivos** —un trámite no tiene resultado que leer—, así que su base son 577, no los
917 puntos del órden del día. Dividir entre 917 mezclaba dos universos y rebajaba el número casi a
la mitad. Importa más de lo que parece: la sección 06 apoya justamente en ese porcentaje el
argumento de que lo que falla no es nuestro proceso sino el registro público que la ley obliga a
llevar. Ahora la base se calcula como la suma de `por_sentido` —no puede desfasarse— y se declara
en pantalla: «25 de 577 decisiones».

**El segundo era de CSS y llevaba tiempo en vivo.** `.medidor-fill` nunca tuvo `background`: sólo
`.medidor-fill.signal` lo definía. La barra sin tono salía **invisible**, así que en el panel el
medidor «Actas procesadas» mostraba 100 % junto a una barra vacía desde que se publicó L4. Se pinta
en `--u-ink`, que era la intención declarada en el comentario de `panel.js` y respeta el
presupuesto de color: la señal se reserva para la profundidad de lectura.

**Poda de prosa.** La primera versión leía como informe, no como página: se recortó cerca de un
cuarto del texto sin quitar una sola afirmación. Frases más cortas, menos subordinadas, ninguna
sección eliminada. Los datos y la estructura son los mismos.

**Y el mecanismo se probó solo.** Al renderizar, la página dijo **640** PDF en el corpus donde el
respaldo escrito a mano decía 636. No era un error: 636 era el conteo de cuando el término tenía
74 actas, y ahora tiene 78. `actas.json` trae 640 filas con 640 `id` únicos, sin duplicados. Se
corrigió el respaldo. **`CLAUDE.md` y `docs/metodologia.md` siguen diciendo 636** en ocho lugares
entre los dos — misma clase de cifra vieja, y ahora está claro por qué nada en prosa debe llevar un
número a mano.

**Pendiente.** El texto de la página afirma que el término tiene 19 actas con el órden del día
modificado y que sus registros están reparados; los 19 resúmenes **siguen sin re-generarse**. La
página no miente —no afirma que estén corregidos— pero la corrida con `resumir_forzar` sigue siendo
la deuda abierta, y hasta que ocurra el acta 48 sigue siendo el `punto_en_conflicto` del término.

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
