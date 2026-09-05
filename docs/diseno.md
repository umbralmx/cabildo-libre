# Diseño — aplicación del sistema Umbral a Actas Abiertas

Registro de cómo se aplicó el manual de marca (`assets/CLAUDE.md`) y
`assets/umbral-engineering.md` a este sitio, y de las decisiones que requirieron
interpretación. Última revisión: **2026-09-04** (sistema Umbral **v2.0.0**).

**Modo: instrumento, en todo el proyecto.**

| Superficie | Archivos | Modo |
|---|---|---|
| Buscador y metodología | `site/*.html` | **instrumento** |
| El tablero (Observable Framework) | `panel/` → `site/panel/` | **instrumento** |

Este registro dijo durante un tiempo «no hay modo instrumento en este proyecto».
Era falso, y de la peor manera: no por un descuido de implementación sino por no
haber leído la tabla de superficies.

### Por qué todo el proyecto va en instrumento (desviación deliberada)

La tabla de superficies de la guía pone `web` en laboratorio, así que poner las
páginas estáticas en instrumento **se aparta de ella**. Queda anotado aquí y no
se disimula.

El razonamiento es el que `desaparecidosmx` usó para revertir exactamente esta
decisión el mismo día que la tomó: *«la tabla de superficies es la regla más
específica, y esta página es un monitor sobre un registro vivo, no una página
sobre el proyecto.»* Aquí aplica igual. `cabildo-libre` no es un micrositio que
habla de un proyecto: es la superficie de consulta sobre el registro de actas de
un ayuntamiento, y en el vocabulario del laboratorio es un **instrumento**. Un
instrumento con la mitad de sus páginas claras y la otra mitad oscuras no es un
instrumento: son dos cosas con el mismo dominio.

Lo que UMB-COL-011 sí exige, y esto cumple, es que el modo sea **uno solo por
artefacto** y que lo fije el medio y no el `prefers-color-scheme` del lector.
Media superficie clara y media oscura es justo el defecto que la regla existe
para evitar, y era el estado en que quedó el proyecto cuando sólo se movió el
panel. `verificar_marca.py` lo comprueba página por página.

**Qué costó el cambio: nada de color.** Ni una regla de `styles.css` se tocó.
Los 63 usos de color de la hoja salen de tokens, y `tokens.css` los redefine bajo
`[data-mode="instrumento"]`; el cambio es un atributo en el `<html>` de cada
página. Eso es exactamente lo que la cadena de tokens existe para permitir, y la
primera vez que este proyecto lo cobra.

**El atributo va en el HTML, no en el JavaScript.** Si lo pusiera un script, la
página pintaría en claro y se oscurecería después, a la vista del lector.

**Contraste: mejora.** La auditoría pasa 44 de 44 pares en los dos modos, y en
instrumento la mayoría mejora — `signal` sobre `base` sube de 4.22:1 a 10.30:1.
El isotipo pasa a la variante `-dark`, que es la marca clara (`#5fd4c4`) para
fondo oscuro.

## Presupuesto de signal — la decisión de más criterio

La regla dice que `signal` se reserva para **el elemento más importante de cada vista**
y que nunca es decorativo. Aquí conviven varios usos, y esta es la lectura que los
justifica: **cada uso de signal marca identidad, una coincidencia, o un estado activo.
Ninguno es decoración.**

| Uso | Justificación |
|---|---|
| Guion bajo del wordmark `umbral_` | Parte de la especificación del logo (§5) |
| Acento del hero («Cabildo de Colima») | §8 concede explícitamente *un* acento de signal al hero de un sitio |
| Coincidencias de búsqueda (`<mark>`) | Son *el hallazgo*: el elemento más importante de la vista de resultados |
| Regla izquierda de la sesión abierta | Especificación de fila destacada (engineering §3) |
| Hover y focus | Especificación de componentes (engineering §3) |

Ajuste consciente: la regla de 4px de la sesión abierta se aplica **sólo al renglón de
resumen**, no a todo el bloque desplegado. Recorrer 800px de barra teal convertía un
marcador de estado en decoración — justo lo que la regla prohíbe.

## Tipografía

- **Space Grotesk 500** en h1, h2 y valores de estadística. Nunca 700 (§4 y lista de
  rechazo §9). Tracking `-0.02em` vía token.
- **IBM Plex Sans** en cuerpo, controles y texto de los puntos de agenda.
- **IBM Plex Mono** en fechas, etiquetas de campo, conteos, cifras y línea de fuente,
  con `tabular-nums` donde hay números que se comparan en columna.
- Escala respetada: h1 `clamp(40px, 5.5vw, 56px)` (rango 40–64), h2 de sección 24px
  (rango 22–26), cuerpo 16–17px con interlínea 1.55, etiquetas 13–14px, mono 12px.
- **Fuentes auto-hospedadas** (`site/assets/fonts/`, 12 archivos woff2, ~260 KB,
  subconjuntos latin y latin-ext para diacríticos del español). Sin dependencia de
  Google Fonts: el manual lo pide para productos que deben funcionar en redes
  gubernamentales o sin conexión.

## Color y forma

- Todos los colores salen de `assets/tokens.css`. **Ningún hex escrito a mano.**
- Sin gradientes, sin sombras, sin esquinas redondeadas (radio 0), sin botones píldora,
  sin negro ni blanco puros. Las reglas de 1px hacen el trabajo estructural.
- Escala de espaciado de 8px (`scale.unit` en tokens.json) en todo el layout.

## Composición

- Medida de texto máxima ~65ch en prosa; los puntos de agenda llegan a 72ch porque son
  texto administrativo denso donde una medida muy corta fragmenta la lectura.
- La línea de tiempo sigue la especificación de tabla: regla superior de 2px en `ink`
  por año, reglas de 1px entre sesiones, fechas en mono.
- Fila de estadísticas siguiendo la especificación de KPI: etiqueta en mono `caption`
  en versalitas, valor en Space Grotesk 500 a 32px. Responde al principio de voz «los
  números cargan el argumento» (§2): la primera cosa concreta que ve quien entra es
  636 sesiones y 6,992 puntos, no una promesa.

## Accesibilidad

- `lang="es"` para pronunciación correcta en lectores de pantalla.
- **Nada codificado sólo por color:** las coincidencias llevan color *más* peso 600
  *más* subrayado; los puntos procedimentales se distinguen por tono pero su texto
  completo siempre está presente y es igualmente buscable.
- Objetivos táctiles ≥44px en controles y renglones de sesión.
- `:focus-visible` con contorno en signal; `prefers-reduced-motion` respetado tanto en
  la animación de despliegue como en el desplazamiento suave.
- Contraste AA con los tokens del modo laboratorio.

## Voz

Español primero. Enunciados completos, sin signos de admiración, sin emoji, sin
palabras de bombo. La metodología nombra la fuente, el método y los vacíos; el estado
vacío de búsqueda explica *por qué* algo puede no aparecer (los PDF son escaneos) en
lugar de sólo decir «sin resultados».

## Desviaciones deliberadas del manual

1. **Sin conmutador ES/EN** en la navegación, aunque §7 lo incluye en el patrón de
   header. Es una herramienta municipal para residentes de Colima; no es un artefacto
   internacional. El manual pide «español primero, inglés para artefactos
   internacionales» — este no lo es.
2. **Sin «Proyectos»** en la navegación: este sitio es un proyecto, no el portal de
   umbral_. La navegación lleva a Datos, Metodología y la fuente oficial.
3. **Wordmark construido en HTML** en lugar de usar `umbral-lockup-light.svg`. El SVG
   del lockup trae el texto como `<text>` y, cargado como `<img>`, no accede a las
   fuentes auto-hospedadas: caería a una sans genérica. El isotipo (sin texto) sí se
   usa como SVG.

## Fase 2 en la interfaz (2026-07-20)

Al integrar OCR y resúmenes al sitio se tomaron dos decisiones de marca:

- **Número de sección en señal-mono.** Los encabezados de sección (`01 Datos`,
  `02 Metodología`) llevan el número en mono, color señal — la firma de encabezado del
  brand book (§Contenido y §Esencia lo usan así). Es un uso estructural de señal, uno por
  sección/vista, sancionado por el propio manual; no gasta el presupuesto de señal de la
  vista principal.
- **El `sentido` no usa señal.** En resultados, la señal ya la lleva el resaltado de la
  coincidencia (`<mark>`). Por eso las etiquetas de sentido (aprobado, aplazado…) van en
  **mono monocromo** (color `muted`/`caption`), no en señal — así no compiten por el único
  elemento señal de la vista. La excepción `rechazado` usa `alert` (el token para lo
  excepcional), y `no_determinable` va en `caption` en cursiva. Esto también cumple «nunca
  codificar por color solamente»: el sentido se lee como palabra, no como color.
- **Aviso de IA visible.** Cada acta con resúmenes muestra una nota: «generados con IA
  sobre texto OCR; pueden contener errores — verifica en el PDF». La honestidad es parte
  de la marca (voz civil-científica), no una nota al pie.

## Fase 3 — el panel por administración (2026-07-25)

`site/panel.html` es la sección de analítica (L4). Tres decisiones de criterio, con su razón:

**1. Ninguna gráfica codifica nada por color.** Se comprobó con el validador de la skill
`dataviz`: el gris `--u-muted` (#6E756F) y el `--u-signal` (#128273) tienen una separación
de **ΔE 1.8 en visión deuteranope y 8.5 en visión normal** — muy por debajo del piso de 15.
Como pareja categórica son indistinguibles, así que **no se usan como pareja**. Cada gráfica
es de una sola serie, en `--u-ink`, y la identidad la cargan la etiqueta de la fila y el
valor en mono. Es también lo que pide la marca (§6.3: etiquetar directo, sin caja de
leyenda), pero aquí la razón es de accesibilidad, no de estilo.

**2. El presupuesto de signal se gastó en un solo elemento de toda la página:** el medidor
de *profundidad de lectura* en §01. Es la cifra de la que dependen todas las demás — el
porcentaje del expediente que el modelo alcanzó a leer— y por eso es lo único resaltado.
Las barras de datos, incluidas las de dinero y asistencia, van en tinta.

**3. El panel se queda en modo laboratorio (light), no en instrumento (dark).** El manual
asigna dark a *dashboards*, pero éste no es una pantalla de monitoreo: es una sección de un
sitio público que se lee seguido del buscador. Cambiar de modo entre dos páginas del mismo
sitio se leería como un error, no como una intención. Desviación deliberada, registrada aquí.

Otras notas de implementación:

- **Los títulos de las gráficas se generan a partir de los datos**, no se escriben a mano,
  para que no puedan quedar desmentidos cuando la cobertura crezca. Son frases que enuncian
  el hallazgo (marca §6.1), no rótulos de tema.
- **Cada gráfica tiene su gemela en tabla** (`<details> → Ver los datos`), que es la ruta
  accesible y también la verificable.
- **Las cifras de dinero grandes se escriben completas** en los títulos, y las abreviadas
  usan millones (`$1,078M`). Se descartó `MM`: para unos lectores es *millones* y para otros
  *mil millones*, ambigüedad que una cifra de dinero público no puede permitirse.
- **Las salvedades van al lado de lo que califican**, al tamaño del texto de cuerpo y con
  regla lateral; las que advierten algo (ventanas fallidas, puntos en conflicto) usan
  `--u-alert` en la regla. Ninguna es nota al pie.
- **La lista de colonias no tiene scroll propio.** Un contenedor con scroll interno se come
  el scroll de la página cuando el cursor cae encima; se muestra un tope de 12 con botón para
  ver las 57.

## Migración al sistema v2.0.0 (2026-09-04)

El sitio se diseñó contra la v1.1.0. La guía llegó a la 2.0.0. Esto es lo que se
adoptó y las llamadas de criterio que hizo falta hacer.

### La capa de componentes, y qué se borró

`components.css` (v1.6.0) es la hoja **escrita a mano** del sistema: los diez
componentes que necesita una superficie de datos. El sitio la carga y **borra su
copia local** de cada forma que ya define.

| Forma | Antes, en `styles.css` | Ahora |
|---|---|---|
| Botón | `.btn-secondary`, cara display | `.u-btn` |
| Campo y selector | reglas propias por control | `.u-input` · `.u-select` |
| Tabla gemela | `.tabla` + `.num` | `.u-table` + `data-numeric` |
| Lista de colonias | `.colonia-item` | `.u-rows` · `.u-row` |
| Fila de KPI | `.stat-value`, cara display | `.u-kpi` |
| Estado vacío | `.colonia-vacio` | `.u-empty` |

La regla que queda para adelante: **si la forma existe en `components.css`, se usa
su clase y no se le vuelve a dar estilo aquí.** Duplicar una regla es como las dos
hojas se separan sin que nadie lo note.

Dos cambios se ven en pantalla:

- **Los KPI pasan a mono tabular.** Estaban en Space Grotesk. Una fila de KPI existe
  para leerse columna contra columna, y las cifras sólo se alinean en mono con
  numerales tabulares (UMB-TYP-004).
- **Los resultados de búsqueda dejan de ser tarjetas.** Eran cajas con relleno
  `panel`, borde y 24px de padding. UMB-LAY-007 dice que una lista de elementos se
  separa con reglas de 1px. Ahora son renglones. El renglón es `display: block` y no
  el flex de `.u-row`, porque un resultado apila metadatos, texto, resumen y enlace
  en vez de emparejar una etiqueta con una cifra; la caja es la misma.

### El marco de gráfica v2.0.0

El subtítulo dice **cómo está construida** la cifra. El cambio no es cosmético: una
suma acumulada y un total anual dibujan curvas distintas con los mismos datos, y el
subtítulo viejo (`geografía · periodo · unidad`) no nombraba ninguna transformación.

La línea de fuente tiene dos lados y ya no lleva licencia ni etiqueta de instantánea.
Las dos se mudaron a la página. La fecha de consulta se lee de `generado` en el
payload — **nunca escrita a mano**, que es la misma disciplina de la página de
metodología.

`figura()` en `panel.js` replica la estructura de `Frame.render` de
`@umbralmx/umbral-plot`: `h3`, `p`, cuerpo, `figcaption`. Mantener la forma idéntica
es lo que permite que esta página y una gráfica de Plot se lean como el mismo sistema
aunque no compartan una línea de código.

### `.fig` es una figura sobre datos; `.explica` es prosa

**La llamada de criterio de esta migración.** La página de metodología tenía cuatro
bloques con el marco de gráfica y sólo uno era una gráfica; los otros tres eran un
encabezado, un párrafo y una tabla de referencia.

Vestir el marco los sometía a UMB-CHT-002 y UMB-CHT-003. No podían cumplirlas con
honestidad: **una tabla que describe nuestro propio proceso no tiene fuente externa**,
y poner «Elaboración propia con datos del Ayuntamiento de Colima» encima de ella le
atribuiría al Ayuntamiento una afirmación que nunca hizo. Cumplir la regla al pie
habría producido una mentira pequeña.

Así que se separaron. `.fig` promete una figura sobre datos y carga con las dos reglas.
`.explica` tiene la misma tipografía y no promete nada. Lo que se movió a `.explica`:
la tabla de las cinco etapas, las dos tablas de «se mide / no se mide» y dos bloques de
prosa. Se quedó en `.fig` la única gráfica real de la página.

### La retícula de puntos

UMB-LAY-009, añadida porque sin ella la retícula sería una excepción no escrita a
UMB-LAY-005 (que prohíbe la ilustración decorativa). Escrita, está acotada: vive detrás
de la página en `baseline` a 22px, el encabezado, la hoja y el pie la tapan con `base`,
y **nunca queda debajo de texto, tabla ni gráfica** — por eso no mueve ningún contraste
medido. Desaparece bajo 980px, donde no hay margen que llenar.

Es la única pieza que se añadió sin haber estado antes. Si estorba, se quita borrando
un bloque.

### Etiquetas en minúsculas

Cinco reglas estaban en versalitas con 0.04em de tracking. UMB-LAY-006 pide mono,
**minúsculas**, en `caption`. Se corrigieron las cinco; el tracking se va con las
versalitas, porque existía para compensarlas.

### La puerta de marca

`processor/verificar_marca.py`. El linter del sistema ya pasaba limpio: la capa
mecánica no era el problema. Lo que no puede ver es el contrato del marco, que vive en
la prosa y en el JS que la genera. La puerta revisa eso, más la **deriva de tokens**:
`assets/tokens.css` llevaba la v1.0 —con `caption` en 2.37:1— mientras el sitio servía
la corregida, y nada comparaba las dos copias.

Las seis comprobaciones se probaron rompiendo el sitio a propósito, una por una. Las
seis dispararon. Una puerta que nunca dispara no es una puerta.

## El panel, reconstruido sobre Observable Framework (2026-09-05)

La guía movió la superficie de tablero de Streamlit a Observable Framework en la
v1.4.0 (ADR-0004), y su tabla de superficies asigna **instrumento** al tablero. El
panel de este proyecto era HTML y JS a mano, en laboratorio. Las dos cosas estaban
mal y ninguna era una elección: eran una lectura que no se hizo.

### Qué se movió y qué no

Sólo el panel cambió de *tecnología*: es el único que necesitaba Observable Plot
y un tiempo de ejecución de tablero. El **modo**, en cambio, es instrumento en
todo el proyecto (ver arriba); dejar las páginas estáticas en laboratorio habría
partido el instrumento en dos.

### El modo vive en tres lugares y tienen que coincidir

Si uno se mueve solo, la página pinta medio clara y medio oscura, o parpadea en
claro antes de oscurecerse:

1. `MODE` en `panel/components/format.js` — gobierna el tema de Plot y los tokens.
2. `data-mode` en `<html>`, que escribe `scripts/copy-static.mjs` **en el HTML
   construido**, no por JavaScript. Si llegara por JS, la página parpadearía.
3. El isotipo: `umbral-isotype-dark.svg`, que es el claro sobre fondo oscuro.

`processor/verificar_marca.py` comprueba los tres, y las comprobaciones se
probaron rompiéndolas una por una.

### Las trampas de Framework que costaron trabajo

Todas están en `docs/framework-notes.md` de `desaparecidosmx`; se siguieron desde
ahí en vez de volver a descubrirlas.

- **`style`, nunca `theme`.** Los temas de Framework derivan cuatro colores con
  `color-mix()` desde un solo primer plano. Un color derivado no llega nunca a
  `contrast.json`, así que la compuerta lo da por bueno sin haberlo medido
  (UMB-COL-012).
- **`globalStylesheets: []`.** Si no se vacía, Framework carga Source Serif 4 de
  Google Fonts, y un CDN filtra la IP de cada lector (UMB-TYP-005).
- **`<html>` sin `lang`.** No con uno equivocado: sin ninguno, que es el caso peor
  de UMB-A11Y-001. Framework no expone la etiqueta, así que se reescribe el HTML
  construido.
- **Las `@font-face` no pueden vivir en la hoja.** El empaquetador de CSS de
  Framework no tiene cargador para `.woff2`. Se inyectan desde `fonts.js` con
  `FileAttachment`, que da la misma URL con hash en `preview` y en `build`.
- **El tope de 640px.** Framework limita toda `<figure>` a 640px y la hoja
  generada levanta el tope **sólo para los hijos directos** de
  `#observablehq-main`. El idioma mínimo pide secciones, así que toda gráfica
  dentro de una `<section>` se quedaba pequeña — bien proporcionada y pequeña, que
  es por qué cuesta verlo. `umbral.css` la exceptúa por clase.
- **Los `import` se separan por lo que esperan.** Framework fusiona todos los de
  un bloque en una celda que resuelve cuando resuelve el más lento. La marca no
  debe esperar detrás del archivo de datos.

### Lo que no cambió

La decisión de que **ninguna gráfica codifique nada por color**. El gris `muted` y
`signal` no se separan como par categórico bajo deuteranopía (ΔE 1.8), así que cada
gráfica sigue siendo de una sola serie y la identidad viene de la etiqueta y de la
cifra en mono. El presupuesto de `signal` se sigue gastando en un solo elemento: el
medidor de profundidad de lectura.

Tampoco cambió el encuadre 2.0.0 ni la regla de no imputar. Lo que cambió es el
tiempo de ejecución debajo de esas decisiones, no las decisiones.

### La URL vieja sigue viva

`site/panel.html` se quedó como redirección a `./panel/`. Los enlaces publicados
antes del cambio siguen resolviendo.

## Lista de verificación previa al lanzamiento

- [x] Modo correcto para el medio (laboratorio/light para sitio web)
- [x] Colores tomados de tokens, no escritos a mano
- [x] Display en Space Grotesk 500; cuerpo en Plex Sans; datos en Plex Mono
- [x] Español primero; fuente nombrada y enlazada
- [x] Nada de la lista de rechazo (§9)
- [x] Contraste AA, sin codificación sólo por color, foco visible, objetivos ≥44px
- [x] Vacíos de datos declarados en pantalla, no ocultos
- [ ] Licencia de datos definitiva — depende de X1 (`docs/x1-terminos-legal.md`)
