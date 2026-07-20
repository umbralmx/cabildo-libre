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
- Todo corre en memoria sobre ~7,000 puntos: no hace falta un índice invertido a esta
  escala, y evitarlo mantiene el sitio sin dependencias.

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

## 9. Procedencia y licencias

Ver `data/SOURCE.md` y, importante, **`docs/x1-terminos-legal.md`**: los Términos y
Condiciones del portal contienen una cláusula que restringe la reproducción y
comunicación pública de sus contenidos. Eso está sin resolver y condiciona qué se puede
publicar y bajo qué licencia. El código es MIT; la estructura que aportamos se comparte
bajo CC BY 4.0; el texto oficial se atribuye a su fuente sin que nosotros pretendamos
licenciarlo.
