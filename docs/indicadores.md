# Indicadores — Fase 3 «The Lens»

> Especificación de los indicadores de análisis por administración. La **fuente de verdad
> máquina-legible** es [`data/indicadores.json`](../data/indicadores.json); este documento la
> explica. Deriva de la nota de producto *El espacio de análisis* (catálogo de ~30 análisis
> posibles). Alcance aprobado: los niveles **`ya`** y **`1 paso`**; los de nivel *externo*
> (bloques de voto por partido, mapa geocodificado, colonias sin mención, búsqueda semántica)
> quedan fuera por ahora.

## Cómo leer un indicador

Cada indicador declara: qué **pregunta** responde, su **definición**, de qué **fuente** sale, su
**cálculo**, su **salvedad** de honestidad, y dos etiquetas:

- **Listo del dato**
  - **`ya`** — se calcula con lo ya extraído (`data/summaries` esquema 2, `data/asistencia`,
    `data/actas`).
  - **`1 paso`** — necesita un campo nuevo de extracción sobre el OCR *existente* (el dato ya está
    en el texto, falta estructurarlo) o un cruce entre sesiones. Ver [Campos nuevos (L5)](#campos-nuevos-l5).
- **Audiencia** — dónde cae en el dial estratégico: **Servicio** (el ayuntamiento lo adopta sin
  fricción), **Transparencia** (sirve a ambos lados), **Rendición de cuentas** (el público se
  inclina, el ayuntamiento resiste). Un indicador puede abarcar un rango.

## Regla de honestidad

Vale para todos: **nunca rellenar un vacío de la fuente por inferencia.** Los agregados declaran su
cobertura; los montos son *lo declarado*, no *el total*; el sentido o el voto ilegible se marca
`no_determinable`, no se adivina; los suplentes se listan, no se funden en el roster.

---

## 💰 Dinero

| id | Indicador | Pregunta | Fuente | Listo | Audiencia |
|----|-----------|----------|--------|-------|-----------|
| M1 | Inversión declarada en el tiempo | ¿Cuánto dinero público se puso sobre la mesa, mes a mes? | `montos[].valor_mxn` + fecha | `ya` | Servicio · Transparencia |
| M2 | Gasto por categoría | ¿En qué se concentra: obra, licencias, finanzas? | `montos` + `categoria` | `ya` | Transparencia |
| M3 | Inversión por colonia | ¿Qué barrios reciben obra y cuáles no? | `obras_detalle[]` | `1 paso` | Transparencia · Rendición |
| M4 | Mayores decisiones económicas | ¿Cuáles fueron los acuerdos de más dinero? | `montos[]` | `ya` | Transparencia · Rendición |
| M5 | Contrapartes externas | ¿Qué empresas firman con el municipio? | `empresas[]` | `1 paso` | Rendición |
| M6 | Cartera de obra pública | ¿Cuántas obras, de qué tipo, en qué calles? | `obras[]` + `categoria` | `ya` | Servicio · Transparencia |

- **M1** — suma de `valor_mxn` por bucket temporal, sobre puntos sustantivos. *No es el presupuesto
  del municipio, sólo lo nombrado en los puntos analizados.*
- **M3** — necesita las filas de la tabla de obras con su colonia y monto (`obras_detalle`). Las
  colonias son menciones no exhaustivas.
- **M5** — la contraparte se nombra tal cual; **no se afirma favoritismo**, sólo se registra la
  recurrencia. (Es la pregunta de "proveedores favoritos", en su forma honesta.)

## ⚖️ Decisiones

| id | Indicador | Pregunta | Fuente | Listo | Audiencia |
|----|-----------|----------|--------|-------|-----------|
| D1 | Ritmo de decisiones | ¿Cuántos asuntos resuelve por sesión y por mes? | `sentido` | `ya` | Servicio · Transparencia |
| D2 | Mezcla de asuntos | ¿De qué se ocupa el cabildo en el fondo? | `categoria` | `ya` | Servicio · Transparencia |
| D3 | Aprobado vs. aplazado | ¿Con qué frecuencia pospone, rechaza o retira? | `sentido` | `ya` | Transparencia |
| D4 | Consenso vs. disenso | ¿Vota unido o dividido, y cambia con el tiempo? | `votacion` + fecha | `ya` | Transparencia · Rendición |
| D5 | Qué se disputa más | ¿Qué tipo de asuntos divide al cabildo? | `categoria` + `votos_en_contra[]` | `1 paso` | Rendición |
| D6 | Seguimiento de aplazados | ¿Qué se pospone y cuándo (o si) regresa? | `sentido` + cruce de sesiones | `1 paso` | Transparencia |

- **D3** — `no_determinable` no es "sin decisión": es "no legible en el OCR".
- **D4** — la *forma* de votación (unánime/mayoría) es distinta del *resultado* (`sentido`).
- **D5** — existe una versión básica `ya` usando sólo `votacion=mayoria`; la versión rica (quién y
  cuántos votaron en contra) es la de un paso.

## 👥 Personas

| id | Indicador | Pregunta | Fuente | Listo | Audiencia |
|----|-----------|----------|--------|-------|-----------|
| P1 | Asistencia por regidor | ¿Quién se presenta —presencial, remoto, con falta? | `asistencia → estados` | `ya` | Transparencia · Rendición |
| P2 | Registro de voto y disidencia | ¿Quién vota en contra, cuánto, en qué? | `votos_en_contra[]` | `1 paso` | Rendición |
| P3 | Abstenciones | ¿Quién se abstiene y ante qué? | `abstenciones[]` | `1 paso` | Rendición |
| P4 | Autoría y patrocinio | ¿Quién presenta más dictámenes? | `comision` + `autor` | `1 paso` | Transparencia |
| P5 | Suplencias | ¿Quién sustituye a quién y cuántas veces? | `asistencia → no_reconocidos` | `ya` | Transparencia |

- **P1** — tasa = `(presente+remoto) / determinables`, **excluyendo `no_determinable`**: un mal
  escaneo no cuenta ni como presencia ni como falta.
- **P2** — sólo cuando el acta nombra explícitamente a los disidentes (*"votos en contra de las
  Regidoras…"*, 15/25 actas). Era el análisis que sub-alcancé antes como "participación demasiado
  ruidosa": no lo es, el acta los nombra.
- **P5** — se reporta el nombre tal cual; no se infiere a qué titular sustituye.

## 🏛️ Institución

| id | Indicador | Pregunta | Fuente | Listo | Audiencia |
|----|-----------|----------|--------|-------|-----------|
| I1 | Actividad por comisión | ¿Qué comisiones producen más trabajo? | `comision` | `1 paso` | Transparencia |
| I2 | Instrumentos de gobierno | ¿Dictámenes, convenios, reglamentos, nombramientos? | `categoria` | `ya` | Servicio · Transparencia |
| I3 | Cadencia de sesiones | ¿Cada cuánto sesiona? ¿Ordinaria/extraordinaria/solemne? | `tipo_sesion` + fecha | `1 paso` | Servicio · Transparencia |
| I4 | Trabajo normativo | ¿Qué reglamentos se reforman o crean? | `reglamentos[]` | `1 paso` | Transparencia |
| I5 | Duración de sesiones | ¿Cuánto dura una sesión, cuántos recesos? | OCR (marcas horarias) | `ya` | Transparencia |

- **I2** — `categoria` aproxima el instrumento; la distinción fina (dictamen vs. acuerdo) se refina
  en L5.
- **I5** — dato escaso: sólo ~5/25 actas registran horas; se muestra sólo donde existe.

## 🗺️ Geografía

| id | Indicador | Pregunta | Fuente | Listo | Audiencia |
|----|-----------|----------|--------|-------|-----------|
| G1 | Atención por colonia | ¿Dónde ha puesto su atención el cabildo, y con cuánto? | `colonias[]` + `obras_detalle[]` | `1 paso` | Transparencia · Rendición |

- **G1** — el ranking básico por menciones ya es `ya`; el de un paso es la normalización a un padrón
  de colonias. El **mapa** geocodificado (G2) queda fuera de alcance: esto es un ranking, no un mapa.

## 🔍 Confianza (meta)

| id | Indicador | Pregunta | Fuente | Listo | Audiencia |
|----|-----------|----------|--------|-------|-----------|
| T1 | Cobertura del procesamiento | ¿Cuánto del término está procesado y con qué profundidad? | `analytics → cobertura` | `ya` | Transparencia |
| T2 | Legibilidad de los documentos | ¿Qué tan legibles son los registros públicos? | `sentido/votacion == no_determinable` | `ya` | Transparencia · Rendición |
| T3 | Enlaces muertos y actas faltantes | ¿Qué documentos ha dejado caer la fuente? | `actas → pdf_url` | `ya` | Rendición |

- **T2** — mide la **calidad documental del ayuntamiento**, no la del proyecto; se enmarca así. Es
  una métrica de rendición de cuentas que ningún otro visor ofrece.
- **T3** — el *link rot* es de la fuente, no del proyecto; los huecos quedan visibles, no se rellenan.

---

## Campos nuevos (L5)

Los indicadores `1 paso` se habilitan con estos campos. Están definidos en `campos_nuevos_L5`
dentro de `data/indicadores.json`. **Todo ya está en el texto OCR; falta estructurarlo.**

### Por punto (se suman al prompt de `summarize_colima.py`)

La ficha de decisión (esquema 3) ya extrae los primeros cuatro; faltan los dos últimos.

| Campo | Estado | Habilita | De dónde sale (frecuencia observada) |
|-------|--------|----------|--------------------------------------|
| `beneficiario` (`{nombre, tipo}`) | ✅ hecho | M5 | Contraparte del acto: empresa (S.A./S. de R.L., 13/25), persona, dependencia |
| `votos_en_contra` (`[{nombre, id}]`) | ✅ hecho | P2, D5 | *"votos en contra de las Regidoras…"* — 15/25 actas |
| `abstenciones` (`[{nombre, id}]`) | ✅ hecho | P3 | Abstenciones nombradas — 11/25 actas |
| `comision` + `autor` (`{nombre, id}`) | ✅ hecho | P4, I1 | *"la Regidora X, Presidenta de la Comisión Y, dio lectura…"* — 23/25 |
| `reglamentos` (`{nombre, accion}`) | ⬜ pendiente | I4 | Reglamentos tocados — 24/25 actas |
| `obras_detalle` (`{obra, colonia, monto}`) | ⬜ pendiente | M3, M6+ | Filas de la tabla de obras |

Los votos, abstenciones y autor se emparejan al roster (`data/regidores-2024-2027.json`) con
`roster_match.py` — la misma lógica tolerante a OCR de `asistencia_colima.py`. Un nombre que no
casa con nadie queda con `id: null` (un suplente o una errata), nunca se fuerza a un titular.

### Por acta (parseo del encabezado, sin LLM)

| Campo | Habilita | De dónde sale |
|-------|----------|---------------|
| `tipo_sesion` | I3 | Encabezado del acta (`ordinaria` / `extraordinaria` / `solemne`) |

### Cruce (en el agregador `build_analytics.py`)

| Lógica | Habilita | Cómo |
|--------|----------|------|
| `aplazados` | D6 | Enlace heurístico del texto del asunto entre sesiones sucesivas, con confianza declarada |

## Próximos pasos

1. **Backfill Tier A** (`procesar.yml` → `resumir_forzar: true`, `lote ≥ 25`) para que los `ya` de
   dinero/categoría no salgan flacos.
2. **L4** — tablero sobre los 15 indicadores `ya`.
3. **L5** — extracción de un paso (campos de arriba) → extender L3 y L4 para los 11 `1 paso`.
