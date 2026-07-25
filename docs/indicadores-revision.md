# Revisión crítica del diccionario de indicadores

> **Fecha:** 2026-07-25 · **Base:** las 25 actas del término 2024-2027 ya procesadas,
> todas en `esquema 3` (ficha de decisión), 269 puntos, 158 sustantivos.
> **Qué es esto:** una prueba de los 26 indicadores de `docs/indicadores.md` contra los
> datos que de verdad salieron, no contra los que se supusieron al escribir el diccionario.
> Tres preguntas por indicador: **¿es útil?** (¿le responde algo a alguien?), **¿es
> factible?** (¿los datos lo sostienen con honestidad?), **¿es pertinente?** (¿sirve a la
> misión — rendición de cuentas sobre decisiones municipales — o es métrica de vitrina?).

---

## 1. El hallazgo que reordena la prioridad

**Sólo el 25 % del texto OCR del término llegó al modelo.** El corte de
`OCR_TEXT_CAP = 45 000` caracteres en `summarize_colima.py` trunca **17 de 25 actas**
(el acta 64 tiene 595 389 caracteres: se leyó el 8 %).

La consecuencia no es difusa, es medible y perfectamente limpia:

| | actas | puntos sustantivos | `sentido = no_determinable` |
|---|---:|---:|---:|
| Actas **truncadas** (>45K) | 17 | 134 | **91 (68 %)** |
| Actas **completas** (≤45K) | 8 | 24 | **0 (0 %)** |

**Cada uno de los 91 puntos sin resultado viene de un acta truncada. Ninguno viene de un
acta leída completa.** No es que el acta no diga qué se aprobó ni que el modelo sea débil:
es que el sentido de la votación se registra al final de cada punto, y esa parte no se
envía. `votacion` está perfectamente acoplada a `sentido` (91 y 91), así que hoy no aporta
señal independiente.

**Costo de arreglarlo: centavos.** El término completo son ~11.4 M caracteres (~3–4 M
tokens); a $0.14/1M de entrada de DeepSeek v4-flash, leer las 74 actas **enteras** cuesta
menos de $1. El límite nunca fue el dinero: es que un acta de 595K caracteres no cabe en
una sola llamada. La solución es dividir el acta en ventanas y unir los resultados por
punto, no subir el tope.

> **Esto es lo primero.** Seis indicadores (`D1 D3 D4 D6 M1 M2`) están hoy calculados sobre
> la cuarta parte del expediente. Construir el tablero antes de arreglarlo es construirlo
> sobre una muestra sesgada hacia las actas cortas.

---

## 2. Veredicto por indicador

`ya` = el diccionario lo daba por listo. **Veredicto** = qué hacer.

| # | Indicador | Útil | Factible hoy | Pertinente | Veredicto |
|---|---|:--:|:--:|:--:|---|
| **M1** | Inversión en el tiempo | sí | **no** — 18 puntos con monto, muy grumoso | sí | **Aplazar** (tras §1); reformular como acumulado, no serie |
| **M2** | Gasto por categoría | sí | **débil** — misma escasez | sí | **Aplazar** (tras §1) |
| **M3** | Inversión por colonia | alto | **no** — unir monto↔colonia hoy sería fabricar | sí | **Aplazar** a `obras_detalle` (bien marcado) |
| **M4** | Mayores decisiones económicas | **alto** | **sí** — 52 montos, todos con valor | alto | **Construir ya** — el mejor del bloque dinero |
| **M5** | Contrapartes externas | alto | sí **con filtro** | alto | **Reformular** — ver §3.1 |
| **M6** | Cartera de obra pública | sí | **no** — 2 puntos `obra_publica`, 12 de 18 obras cortadas a 80 chars | sí | **Corregir el diccionario**: dice `ya`, no lo es |
| **D1** | Ritmo de decisiones | medio | parcial | medio | **Reformular** como *puntos por sesión*, no "decisiones" |
| **D2** | Mezcla de asuntos | sí | **sí** | sí | **Construir ya**; absorbe I2 |
| **D3** | Aprobado vs. aplazado | alto | **comprometido** — 57/10/91 | alto | **Aplazar** (tras §1) — ver §3.2 |
| **D4** | Consenso vs. disenso | alto | **no** — colineal con la legibilidad | alto | **Aplazar** (tras §1) |
| **D5** | Qué se disputa más | sí | **débil** — la fila superior es una tasa de 0.5 sobre **n=2** | alto | **Reformular** con n mínimo; conteos, no tasas |
| **D6** | Seguimiento de aplazados | **alto** | tras §1 | **alto** | **Aplazar, luego priorizar** — es lo más valioso del set |
| **P1** | Asistencia por regidor | **alto** | **sí** — 25/25 sesiones, 12–13 de 13 colocados | alto | **Construir ya** — el indicador más sólido |
| **P2** | Registro de voto y disidencia | **alto** | sí, **como piso** | **alto** | **Construir** con el encuadre de §3.3 |
| **P3** | Abstenciones | sí | sí | sí | **Fusionar en P2** (misma fuente, misma fila, misma salvedad) |
| **P4** | Autoría y patrocinio | medio | sí | **riesgoso** | **Reformular o descartar** — ver §3.4 |
| **P5** | Suplencias | medio | **sí** — 1 caso real | sí | **Construir** — barato y es una historia de integridad del dato |
| **I1** | Actividad por comisión | sí | **con un paso** — 18 cadenas, 4 grupos de variantes | sí | **Reformular** — necesita catálogo canónico (§3.5) |
| **I2** | Instrumentos de gobierno | medio | sí | medio | **Fusionar en D2** — es la misma distribución de `categoria` |
| **I3** | Cadencia de sesiones | sí | **sí, con cobertura total** | sí | **Construir ya** — ver §3.6 |
| **I4** | Trabajo normativo | sí | no — falta `reglamentos` | sí | **Aplazar** a L5 (bien marcado) |
| **I5** | Duración de sesiones | **bajo** | sí y barato (regex, 25/25 inicio) | **riesgoso** | **Degradar** a dato descriptivo; nunca métrica de desempeño |
| **G1** | Atención por colonia | **alto** | parcial — 57 colonias, 18 % de puntos | alto | **Construir** con "menciones, no exhaustivo"; ver N2 |
| **T1** | Cobertura del procesamiento | **alto** | **sí** | **alto** | **Construir ya y ponerlo arriba**, no al pie |
| **T2** | Legibilidad de documentos | alto | **sí, ahora mejor** | alto | **Reformular** con la métrica N1 |
| **T3** | Enlaces muertos y faltantes | sí | **sí, cobertura total** | sí | **Construir**; separar los huecos de numeración como señal propia |

**Resumen:** de los 15 marcados `ya`, **6 se sostienen hoy** (M4, D2, P1, I3, T1, T3),
**5 necesitan reformularse** (M5, D1, D5, I1, T2), **3 hay que aplazar pese a la etiqueta**
(D3, D4, M6 — M6 está mal clasificado en `data/indicadores.json`) y **1 conviene degradar** (I5).

---

## 3. Los que hay que cambiar, y por qué

### 3.1 M5 — «contrapartes externas» hoy devuelve dependencias internas
Las primeras filas son *H. Congreso del Estado* (3), *Tesorería Municipal* (2, $63.4M) y
*Gobierno del Estado*. Eso no responde la pregunta del indicador (*¿qué empresas firman
con el municipio?*). **Arreglo:** filtrar por `beneficiario.tipo == "empresa"` para la
vista de contrapartes y publicar las dependencias como una vista aparte —*a qué otras
instancias de gobierno se dirige el acto*—, que es una pregunta distinta y también válida.

### 3.2 D3/D4 — una tasa sobre lo legible se leerá como una tasa sobre el cabildo
Hoy saldría "85 % de aprobación" y "88 % por unanimidad". Ambas son ciertas *sobre los 67
puntos cuyo resultado alcanzamos a leer*, y ninguna lo es sobre el cabildo. Es exactamente
el error que el proyecto se comprometió a no cometer. Con §1 resuelto dejan de ser
frágiles; antes de eso, no publicarlas como porcentaje.

### 3.3 P2 — es un piso, no un conteo
Hoy: Azucena López Legorreta 6 en contra / 5 abstenciones, Diana Gabriela Vizcaíno 5 / 3,
**y los otros 11 integrantes en cero**. El cero no significa "nunca disintió": significa
que ninguna de las actas leídas la nombró disintiendo — y sólo el 4 % de los puntos nombra
a alguien en contra, sobre el 25 % del texto. **El tablero debe decir "al menos N veces",
nunca "N veces"**, o convertirá un vacío documental en un perfil político.

### 3.4 P4 — mide quién preside, no quién trabaja
Encabezan la síndica (16 dictámenes) y el presidente municipal (13), muy por encima del
resto. Lo más probable es que refleje **quién preside y da lectura**, no autoría. Publicarlo
como "quién hace el trabajo" sería una inferencia que el acta no sostiene. **O se excluye a
quien preside, o el indicador se cae.**

### 3.5 I1 — 18 cadenas que son menos comisiones
*Comisión de Comercio, Mercados y Restaurantes* (6) y *Comisión de Comercios, Mercados y
Restaurante* (3) son la misma. Hay 4 grupos con variantes de grafía, más las *comisiones
conjuntas* (un punto con dos o tres comisiones). **Arreglo:** un catálogo canónico de
comisiones con variantes, igual que `data/regidores-2024-2027.json` resolvió los nombres —
una tarea manual de una sola vez.

### 3.6 I3 — el único indicador que no depende del OCR
Las fechas de las 74 actas del término (y de las 636 del corpus) vienen de la Fase 1. Y
`tipo_sesion` resultó **extraíble por regex, sin LLM**: 24 de 25 actas lo declaran en el
encabezado (*"Sesión Ordinaria/Extraordinaria"*), y la hora de inicio aparece en 25 de 25,
la clausura en 24 de 25. Es cobertura casi total a costo cero: constrúyase primero.

---

## 4. Indicadores nuevos propuestos

| # | Indicador | Qué responde | Fuente | Costo |
|---|---|---|---|---|
| **N1** | **Profundidad de lectura** | ¿Qué proporción del expediente alcanzó a leerse? *(hoy: 25 %)* | `len(ocr)` vs. lo enviado | cero |
| **N2** | **Qué se decidió en mi colonia** *(lista, no gráfica)* | La pregunta con la que nació el proyecto | `colonias[]` + resumen | cero |
| **N3** | **Concentración de contrapartes** | ¿Cuánto del dinero declarado va al top 1/3/5 de empresas? | `beneficiario` + `montos` | cero |
| **N4** | **Puntos con dinero pero sin cifra** | ¿Cuántas decisiones de gasto no declaran monto? *(hoy 33 de 49 = 67 %)* | `categoria` + `montos` | cero |
| **N5** | **Puntualidad documental** | ¿Cuánto tarda el ayuntamiento en publicar el acta? | fecha de sesión vs. publicación | un paso de datos |
| **N6** | **Proporción de sesiones extraordinarias** | Señal de gobernanza: convocatoria con menos aviso | `tipo_sesion` (regex) | cero |

**N1 es la salvedad que sostiene todo el tablero.** Hoy cada gráfica lleva su `cobertura`
en actas (25 de 74); ninguna dice que de esas 25 se leyó un cuarto. Es el número más
honesto que podemos publicar y el que hace creíbles a los demás.

**N2 devuelve la sección analítica al trabajo #1 del proyecto.** El diccionario es todo
gráficas; pero la prioridad acordada es *encontrar decisiones*, y la pregunta original era
*"¿cuándo se aprobó la obra de mi colonia?"*. Una lista filtrable por colonia, dentro del
panel, sirve a esa pregunta mejor que cualquier barra.

**N4 convierte una carencia en un hallazgo.** 33 de 49 puntos de categorías de dinero no
declaran cifra alguna. *Advertencia:* hoy una parte de ese 67 % es **nuestro** truncamiento,
no opacidad del acta. Sólo es publicable **después** de §1; entonces sí es un dato sobre el
registro municipal, no sobre nuestra tubería.

**N3 hoy sale degenerado** (una empresa concentra el 100 % del monto declarado a empresas)
por la misma razón. Con §1 resuelto es la métrica clásica de rendición de cuentas.

**N5 requiere un dato que no tenemos:** la fecha de publicación. Candidato razonable es el
`Last-Modified` del PDF en el servidor, con la salvedad explícita de que es una marca del
servidor y no una fecha oficial. Vale la pena porque mide el cumplimiento del ayuntamiento,
cubre las 636 sesiones y no necesita OCR.

---

## 5. Secuencia recomendada

1. **Arreglar el corte de 45K** (ventanas por acta + unión por punto). Desbloquea D1, D3,
   D4, D6, M1, M2, N3, N4 de una sola vez y cuesta centavos. **Antes que cualquier gráfica.**
2. **Construir L4 sobre lo que ya se sostiene:** T1 + N1 arriba (cobertura y profundidad),
   P1, M4, D2, I3, G1/N2, P5, T3.
3. **Los pasos manuales de una vez:** catálogo canónico de comisiones (I1); decidir si P4
   se reformula o se cae.
4. **Después del corte:** D3, D4, D6, M1, M2, N3, N4.
5. **L5 pendiente:** `obras_detalle` (M3, M6) y `reglamentos` (I4).

## 6. Cambios pendientes en `data/indicadores.json`

Sin aplicar todavía — el diccionario es la fuente de verdad y conviene decidirlos:

- **M6**: `listo: "ya"` → `"1_paso"` (los datos no lo sostienen).
- **P3**: fusionar en P2; **I2**: fusionar en D2.
- **I5**: degradar; añadir la salvedad de interpretación.
- **M5**: añadir el filtro por `tipo` a la definición.
- Añadir **N1–N6**.
