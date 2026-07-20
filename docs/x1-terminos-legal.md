# X1 — Revisión de los Términos y Condiciones del portal de Colima

**Fecha de revisión:** 2026-07-20 · **Estado: BLOQUEANTE ANTES DE LANZAR — requiere decisión humana**

> Esto **no es asesoría legal**. Es un resumen de lo que dice el documento y de las
> consideraciones en tensión, preparado para que una persona (idealmente con apoyo
> legal) tome la decisión. No lo tomes como un go/no-go resuelto.

**Documento revisado:** [Términos y Condiciones del Ayuntamiento de Colima](https://www.colima.gob.mx/portal2016/wp-content/uploads/2019/02/ayuntamiento-de-colima-terminos-y-condiciones-1.pdf)
(PDF de 3 páginas, enlazado al pie del portal; sí tiene capa de texto).

## 1. La cláusula que nos afecta directamente

Bajo «Derechos y responsabilidades», textualmente:

> «Quedan prohibidas la reproducción (excepto para uso privado, de investigación o
> estudio), la transformación, distribución, comunicación pública y en general
> cualquier otra forma de explotación, por cualquier procedimiento, de todo o parte
> de los contenidos de este portal, como también de su diseño, métodos de selección
> o formas de presentación de los recursos y materiales incluidos del mismo.»

Leída de forma literal, esta cláusula prohíbe exactamente lo que hace este proyecto:
**reproducir y comunicar públicamente** el texto de los órdenes del día, y
**distribuirlo** como JSON/CSV descargable. La excepción de «uso privado, de
investigación o estudio» ampararía el análisis interno, pero publicar un sitio web
abierto es *comunicación pública*.

## 2. La cláusula de enlaces (menor, pero atendible)

- Prohíbe dar a entender que el Ayuntamiento «autoriza, interviene, avala, promociona,
  participa o ha supervisado» los contenidos del sitio que enlaza.
  → **Ya cumplimos**: la metodología es explícita en que esto es un proyecto
  independiente, y no usamos escudo, logo ni identidad del ayuntamiento.
- Prohíbe enlazar desde páginas con contenido ilícito, racista, pornográfico, etc.
  → No aplica.
- «no se podrá incluir ninguna marca comercial o signo diferente de esa dirección URL»
  al establecer el enlace. Redacción ambigua; parece referirse a no sustituir la URL
  por una marca. Nuestros enlaces apuntan a la URL real del PDF. → Sin conflicto aparente.

## 3. Consideraciones en sentido contrario (por qué esto no es un «no» automático)

Ninguna de estas es una conclusión; son los argumentos que un abogado tendría que pesar.

- **Los textos oficiales no son objeto de derecho de autor.** La Ley Federal del Derecho
  de Autor (art. 14) excluye de protección los textos legislativos, reglamentarios,
  administrativos y judiciales. Un acta de cabildo es un acto administrativo de un
  órgano colegiado. Si el contenido no es protegible, unos Términos y Condiciones no
  pueden crear un derecho de autor que la ley no otorga.
- **Son información pública de oficio.** Las actas de cabildo están sujetas a las
  obligaciones de transparencia de la legislación mexicana en la materia: su razón de
  ser es ser públicas y consultables, no restringidas en su reutilización.
- **Naturaleza contractual, no autoral.** Aun sin derecho de autor, unos T&C pueden
  operar como condición de uso del portal. El incumplimiento sería un asunto
  contractual/administrativo, no una infracción de copyright.
- **Riesgo práctico.** El escenario realista más probable es una solicitud de retiro,
  no un litigio. Aun así, el costo reputacional para umbral_ de una disputa pública
  con un ayuntamiento es real y hay que decidirlo con los ojos abiertos.

## 4. Efecto inmediato sobre lo que ya construimos

**La licencia que anunciábamos sobre los datos era demasiado afirmativa.** Estábamos
declarando los datos como CC BY 4.0; no está claro que tengamos el derecho de otorgar
esa licencia sobre contenido de terceros. Ya se ajustó la redacción del sitio y de
`data/SOURCE.md` para:

- licenciar bajo MIT **el código**, que sí es nuestro;
- licenciar bajo CC BY 4.0 **la compilación y estructura** que aportamos (el trabajo de
  parseo y organización), sin pretender licenciar el texto oficial subyacente;
- atribuir el contenido al Ayuntamiento de Colima y enlazar siempre al original.

Esto es reversible en cuanto X1 se resuelva en un sentido u otro.

## 5. Caminos posibles (a decidir por el humano)

| Opción | Qué implica | Costo / tiempo |
|---|---|---|
| **A. Preguntar formalmente** | Solicitud de acceso a la información / escrito a la Unidad de Transparencia pidiendo confirmación de que las actas pueden republicarse, o pidiendo los datos por esa vía (lo que daría una procedencia limpia y un derecho de reúso explícito). | Semanas; es el camino más sólido |
| **B. Consultar a una organización de derechos digitales** | R3D o Artículo 19 México acompañan este tipo de trabajo cívico y suelen orientar sin costo. Da una lectura experta antes de exponerse. | Días–semanas; bajo costo |
| **C. Publicar apoyándose en la no-protegibilidad + transparencia** | Lanzar con atribución clara, sin marca del ayuntamiento, sin sugerir aval, y con un plan de respuesta a una eventual solicitud de retiro. | Inmediato; riesgo asumido |
| **D. Modo índice** | Publicar metadatos y enlaces, y mostrar sólo fragmentos breves en los resultados, sin descarga masiva del texto. Reduce exposición, pero debilita el producto y el principio de devolver los datos al público. | Inmediato; producto más pobre |

**Sugerencia de secuencia:** iniciar **A y B en paralelo** (no bloquean nada más del
desarrollo) y, mientras llega respuesta, decidir conscientemente entre **C** y **D**
para el lanzamiento. A y B son baratos y convierten una apuesta en una posición
documentada.

## 6. Lo que este proyecto ya hace bien, pase lo que pase

- Enlaza siempre al documento original en el servidor del ayuntamiento; no lo sustituye
  ni lo re-hospeda (no guardamos copias de los PDF).
- No usa identidad gráfica ni escudo del ayuntamiento, ni sugiere aval.
- Declara su método, su fuente y sus vacíos de forma explícita.
- No recopila datos personales de las personas usuarias.
