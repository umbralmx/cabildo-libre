# Revisión del diccionario de indicadores — 2026-08-13

> Fase 3 está **en pausa** mientras se contesta esto. `docs/indicadores.md` describe 26
> indicadores que inventamos nosotros, mirando nuestros propios datos. Esta revisión los
> contrasta contra **referencias externas** y contra **el texto OCR que ya tenemos y no
> estamos usando**. No propone tablero nuevo: propone qué debe entrar al diccionario antes
> de volver a construir.
>
> Las coberturas que aparecen abajo están **medidas sobre las 78 actas del término**, no
> estimadas. Los conteos por expresión regular sobre OCR ruidoso son un **piso**, no un
> censo: cuentan las actas donde la señal se lee, y el OCR pierde algunas.

---

## 1. Qué existe allá afuera

Buscamos dos cosas distintas y conviene no confundirlas: **estándares de datos** (qué forma
debe tener el dato) y **marcos de evaluación** (cómo se califica a un cuerpo colegiado).

### Estándares de datos

| Referencia | Qué es | Qué nos aporta |
|---|---|---|
| **[Popolo](https://www.popoloproject.com/specs/)** | Estándar internacional de datos legislativos. Clases `Person`, `Organization`, `Membership`, `Event`, `Motion`, `VoteEvent`, `Vote`. | **El calce más cercano a lo que ya construimos.** Nuestro roster, `asistencia` y `votos_en_contra` mapean casi uno a uno. Adoptar sus nombres hace el dato portable y comparable sin rehacer nada. |
| **[Open Civic Data](https://open-civic-data-docs.readthedocs.io/en/latest/proposals/0007.html)** | Popolo aplicado a municipios, por el equipo de Open States. | Precedente de que Popolo aguanta el nivel municipal, que era la duda. |
| **[Councilmatic](https://www.councilmatic.org/)** · **[Council Data Project](https://www.researchgate.net/publication/356737113_Council_Data_Project_Software_for_Municipal_Data_Collection_Analysis_and_Publication)** | Productos abiertos que hacen nuestro trabajo en ciudades de EE. UU. | Comparación de funciones, no de código: ellos parten de video y minutas ya estructuradas; nosotros de PDF escaneado. Nuestro problema es más duro y ellos no lo resuelven. |
| **[OCDS](https://standard.open-contracting.org/)** | Estándar de contrataciones abiertas. | Sólo si algún día entramos a contratos. Hoy no. |

### Marcos de evaluación

| Referencia | Qué es | Qué nos aporta |
|---|---|---|
| **[ILTL](https://transparencialegislativa.org/indice/)** — Índice Latinoamericano de Transparencia Legislativa | 48 indicadores en 4 dimensiones: *Normatividad*, *Labor Legislativa*, *Presupuesto y Gestión Administrativa*, *Atención y Participación Ciudadana*. Escala 0–100. | **El referente regional más cercano.** Está hecho para congresos, pero sus cuatro dimensiones se trasladan a un cabildo sin violencia. Sirve para ver **qué no estamos midiendo**. |
| **[IMCO — IIPM](https://imco.org.mx/indice-informacion-presupuestal-municipal/)** | Índice de Información Presupuestal Municipal: ~80 criterios binarios sobre 453 municipios. | Municipal, mexicano y **binario**: cada criterio se cumple o no, todos pesan igual. Es el mejor modelo para nuestra familia *Confianza*, que hoy reporta porcentajes difíciles de leer. |

---

## 2. Lo que el contraste revela

### 2.1 Ya hablamos Popolo sin saberlo

| Nuestro campo | Clase Popolo | Nota |
|---|---|---|
| `data/regidores-2024-2027.json` | `Person` + `Membership` | `variantes_ocr` no tiene equivalente y debe quedarse: es nuestro, y es honesto. |
| `comision` | `Organization` | Popolo modela comisiones como organizaciones con membresías. |
| una sesión (`acta`) | `Event` | `tipo_sesion` cae en `Event.classification`. |
| un punto del órden | `Motion` | Popolo sólo estandariza `text` y `classification` — nuestra `categoria` es exactamente `classification`. |
| `sentido` + `votacion` | `VoteEvent` | `result` y `counts`. |
| `votos_en_contra`, `abstenciones` | `Vote` | Popolo tiene `option: yes/no/abstain`. Nosotros sólo nombramos disidentes y abstenciones, nunca el «a favor» por omisión — **eso es más honesto que el estándar** y hay que documentarlo como desviación deliberada. |

**Conclusión:** no hay que rehacer el modelo. Hay que **nombrar** lo que ya tenemos con los
nombres de Popolo y anotar las dos desviaciones (`variantes_ocr`, el voto a favor no inferido).
Es trabajo de documentación, no de datos.

### 2.2 El hueco que el ILTL deja ver

Nuestros 26 indicadores repartidos en las cuatro dimensiones del ILTL:

| Dimensión ILTL | Nuestros indicadores | Estado |
|---|---|---|
| Labor Legislativa | D1–D6, I1–I5, P2–P4, M6 | **Saturado.** Aquí vive casi todo. |
| Presupuesto y Gestión Administrativa | M1, M2, M4, M5, M3 | Cubierto, aunque flaco. |
| Atención y Participación Ciudadana | *(ninguno)* | **Vacío.** |
| Normatividad | I4 (parcial) | Casi vacío — y en parte no nos toca: evalúa la ley, no al cuerpo. |

**El vacío es real y el dato para llenarlo ya está.** «Uso de la voz / de la palabra» aparece
en **41 de 78 actas (53 %)** y ciudadanos identificados como tales en **12 de 78 (15 %)**. El
diccionario descartó esto como *Tier C — «demasiado ruidoso para ser honesto»*. Medido, no lo
es: más de la mitad de las sesiones registran quién pidió la palabra. Esa decisión merece
revisarse, acotada a **quién habló**, sin intentar resumir qué dijo.

### 2.3 T2 no mide nuestra calidad: mide su cumplimiento

**Verificado 2026-08-13 contra el texto de la ley**, no contra resúmenes de terceros. **Ley de
Transparencia y Acceso a la Información Pública del Estado de Colima**, reforma publicada en el
Periódico Oficial *El Estado de Colima* el **16 de agosto de 2025**, **artículo 34, numeral 1,
fracción III** — obligaciones específicas de los Ayuntamientos, adicionales a las 47 fracciones
comunes del artículo 30:

> «Las **actas de sesiones de cabildo**, los **controles de asistencia** a las sesiones de
> cabildo y el **sentido de votación** de las y los miembros del Cabildo sobre las iniciativas
> o acuerdos discutidos»

Las tres cosas, en una sola fracción, y son **exactamente las tres que extrae nuestro
pipeline**: `data/summaries` (el acta y sus acuerdos), `data/asistencia` (el pase de lista) y
`sentido` + `votos_en_contra` + `abstenciones` (el sentido de votación).

Eso reencuadra T2. Hoy se presenta como «legibilidad de los documentos». En realidad es **una
medición de cumplimiento de una obligación legal nombrada**: cuando el sentido del voto no es
determinable, no es que nuestro OCR falle — es que **el registro público no permite saber cómo
votó el cabildo**, que es literalmente lo que el artículo 34.1.III manda que se pueda saber. Es
el indicador más fuerte del proyecto y está subvendido.

**Y hay una obligación vecina que nadie está mirando.** El mismo artículo 34, **fracción II**,
obliga al Ayuntamiento a transmitir **las sesiones de cabildo en vivo** por su página oficial y
a **almacenar ahí las videograbaciones** para consulta. Dos consecuencias, en este orden:

1. **Es un indicador de cumplimiento comprobable** desde fuera, y muy legible para el público:
   ¿existen las transmisiones? ¿siguen consultables? Encaja en la familia *Confianza*.
2. **Si el video existe y es consultable, cambia el techo del proyecto.** Hoy dependemos de OCR
   sobre PDF escaneado porque asumimos que el acta es la única fuente. Un archivo de video con
   audio abre la puerta a transcripción —que es lo que hace citymeetings.nyc, nuestra
   referencia— y a la dimensión de *participación ciudadana* que el ILTL nos marca vacía.

**Comprobación parcial, 2026-08-13.** La página de actas
(`colima.gob.mx/portal2016/actas-de-cabildo/`) **no enlaza video alguno**: es un repositorio de
PDF y nada más. La fracción II pide que las videograbaciones queden almacenadas «en la misma»
página oficial, así que esto es indicio, pero **no basta para afirmar incumplimiento**: el
Ayuntamiento tiene canal de YouTube y las sesiones podrían estar ahí. **No se comprobó.** Hasta
que alguien revise el canal sesión por sesión y lo contraste con las 78 fechas del término, esto
se queda como pregunta abierta, no como hallazgo. Es la comprobación de mayor palanca que queda
pendiente y no cuesta dinero, sólo tiempo.

> ⚠️ Sigue **sin verificar** la otra afirmación que se manejó: que el reglamento municipal
> obligue a cada munícipe a manifestar el sentido de su voto y a **razonar el voto en contra**.
> Eso está en la normativa municipal (Reglamento del Gobierno Municipal / Ley del Municipio
> Libre), no en la ley de transparencia, y no se ha cotejado. De sostenerse, habilita un
> indicador nuevo: *¿cuántos votos en contra vienen razonados?* No entra al sitio sin cotejo.

---

## 3. Lo que el texto ya guarda y no estamos usando

Medido sobre las 78 actas del término.

| Señal | Actas | ¿En el diccionario? |
|---|---|---|
| `tipo_sesion` | **78/78 (100 %)** | I3 — **ya construido** (`orden_del_dia.py`), sin modelo |
| Leyes o reglamentos citados | 75/78 (96 %) | I4, parcial |
| Licencias de bebidas alcohólicas | 48/78 (61 %) | no — **el asunto más frecuente del cabildo** |
| Convenios y contratos | 42/78 (53 %) | no |
| Uso de la voz (quién habla) | 41/78 (53 %) | no — descartado como Tier C; ver §2.2 |
| Claves catastrales (predios) | 34/78 (44 %) | no — exactas, sin ruido, geocodificables después |
| **Dispensa de trámite o de lectura** | **34/78 (44 %)** | **no — nuevo** |
| Cuenta pública | 30/78 (38 %) | no |
| Hora de inicio | 28/78 (36 %) | I5 (el diccionario dice 20 %; es más) |
| **Órden del día modificado en sesión** | **19/78 (24 %)** | **no — nuevo** |
| **Licitación o adjudicación directa** | **19/78 (24 %)** | **no — nuevo** |
| Reforma de reglamentos | 19/78 (24 %) | I4 |
| Receso | 12/78 (15 %) | I5 |
| **Voto de calidad del presidente** | **4/78 (5 %)** | **no — raro y de altísimo valor** |
| **El acta se contradice a sí misma** | **4/78 (5 %)** | **no — nuevo, familia Confianza** |

---

## 4. La familia que falta: **Procedimiento**

Las cinco señales nuevas no son temas sueltos: todas miden **cómo el cabildo controla su
propio proceso**. Ninguna cabe en Dinero, Decisiones, Personas, Institución ni Geografía. Se
propone una sexta familia.

| id | Indicador | Pregunta | Fuente | Listo |
|----|-----------|----------|--------|-------|
| **R1** | Modificación del órden del día | ¿Con qué frecuencia se retiran o incorporan asuntos ya convocados, y quién lo pide? | `orden_del_dia.peticiones` | **ya** |
| **R2** | Peticiones concedidas y negadas | ¿El pleno concede siempre lo que un munícipe pide retirar? | `votacion_de_la_modificacion` | **ya** |
| **R3** | Dispensa de trámite o lectura | ¿Con qué frecuencia se acorta el procedimiento? | 1 paso (OCR) | 1 paso |
| **R4** | Voto de calidad | ¿Cuántas veces desempata el presidente, y en qué? | 1 paso (OCR) | 1 paso |
| **R5** | Método de adjudicación | ¿Licitación o adjudicación directa? | 1 paso (OCR) | 1 paso |

**R1 y R2 ya son calculables hoy**: `processor/orden_del_dia.py` los produce sin modelo y sin
costo. R2 tiene además un caso probado que lo justifica — en el **acta 41** el cabildo aprobó
retirar el Séptimo Punto y **negó** retirar el Sexto. Suponer que toda petición prospera habría
sido falso.

**Salvedad de honestidad de la familia.** Retirar un asunto del órden del día no es indebido:
puede corregir un error, faltar un dictamen o pedirlo la propia comisión. El indicador **cuenta
y nombra, no juzga**, igual que M5 con los proveedores recurrentes.

### Y una nueva de Confianza

| id | Indicador | Pregunta | Fuente | Listo |
|----|-----------|----------|--------|-------|
| **T4** | Contradicciones internas del acta | ¿El documento se contradice a sí mismo? | `tipo_sesion.concuerdan` | **ya** |

Las actas **2, 8, 40 y 59** declaran un tipo de sesión en el encabezado y el contrario en el
bloque de firmas, con OCR limpio en ambos. No es ruido nuestro: es el registro público en
desacuerdo consigo mismo, y el tipo de sesión gobierna reglas distintas de convocatoria y
quórum. Es el mismo argumento de T2 —medimos la calidad del registro, no la nuestra— y ningún
otro visor lo ofrece.

---

## 5. Lo que medimos y **no** vale la pena construir

Se deja escrito para que nadie lo vuelva a proponer.

- **Rezago en la aprobación de actas.** Parecía un buen indicador de disciplina. Medido: el
  cabildo aprueba su acta anterior al corriente en **75 de 76 sesiones**; el rezago promedio es
  de **0.03 actas** y el peor caso son 2. **No hay señal.** Lo que sí hay: 49 de 76 sesiones
  aprueban **varias actas de golpe** (hasta 5), que es un dato de cadencia y pertenece a I3.

---

## 6. Orden de trabajo propuesto

1. **Reparar antes de ampliar.** Volver a resumir las 19 actas con órden del día modificado
   (~$0.15). Mientras no se haga, cualquier indicador que agregue por `n` de punto arrastra el
   error del acta 48. **Esto es lo primero.**
2. **Cobrar lo ya construido** — R1, R2, T4 e I3 (`tipo_sesion`) salen de `data/estructura/`
   sin costo ni modelo. Sólo falta agregarlos y mostrarlos.
3. **Renombrar a Popolo** y documentar las dos desviaciones deliberadas (§2.1). Documentación,
   no migración.
4. **Verificar el piso legal** (§2.3) y, si se sostiene, reencuadrar T2 como cumplimiento.
5. **Reabrir el Tier C** acotado a *quién pidió la palabra* — es el único camino a la dimensión
   del ILTL que hoy está vacía.
6. **Después** de todo lo anterior, L5 y el resto de los `1 paso`.

---

## Fuentes

[Popolo](https://www.popoloproject.com/specs/) ·
[Open Civic Data](https://open-civic-data-docs.readthedocs.io/en/latest/proposals/0007.html) ·
[Councilmatic](https://www.councilmatic.org/) ·
[Council Data Project](https://www.researchgate.net/publication/356737113_Council_Data_Project_Software_for_Municipal_Data_Collection_Analysis_and_Publication) ·
[ILTL — Red Latinoamericana por la Transparencia Legislativa](https://transparencialegislativa.org/indice/) ·
[IMCO — Índice de Información Presupuestal Municipal](https://imco.org.mx/indice-informacion-presupuestal-municipal/) ·
[Ley de Transparencia y Acceso a la Información Pública del Estado de Colima](https://www.gob.mx/cms/uploads/attachment/file/173597/Ley_transparencia_acceso_informacion_publica_colima.pdf)
