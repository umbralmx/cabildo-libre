# Bitácora de desarrollo — Actas Abiertas

> Registro cronológico de lo construido, lo que costó trabajo y lo que sigue.
> Complementa a `CLAUDE.md` (contexto y alcance) y a `docs/metodologia.md` (cómo se
> produce el dato). Entradas más recientes primero. Fechas absolutas.

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
