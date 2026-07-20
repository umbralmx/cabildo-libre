# SOURCE.md — data/actas.json · data/actas.csv

## Origen

- **Fuente:** https://www.colima.gob.mx/portal2016/actas-de-cabildo/ — índice HTML de
  actas de cabildo del Ayuntamiento de Colima (texto del órden del día + enlaces PDF).
- **Transformación:** `scraper/scrape_colima.py`, sin dependencias y sin ediciones
  manuales. Cada registro es reproducible desde el índice.
- **Primera descarga:** 2026-07-19. Última revisión de este archivo: 2026-07-20.
- **Actualización:** automática vía `.github/workflows/actualizar.yml` (lunes y jueves).
  El campo `generado` del JSON indica la corrida que produjo el archivo.
- **Método completo:** `docs/metodologia.md`.

## Contenido

| | |
|---|---|
| Sesiones | 636 (de 640 filas; 4 duplicados en la fuente) |
| Puntos de agenda | 6,992 |
| Cobertura | 2012–2026, 5 administraciones |
| `actas.json` | Un objeto por sesión, con `agenda_items[]` anidados |
| `actas.csv` | Formato largo: un renglón por punto de agenda |

Campos: `id`, `fecha` (ISO), `fecha_texto`, `no_acta`, `no_acta_texto`, `periodo`,
`agenda_items[]` (`n`, `numeral`, `texto`), `pdf_url`, `orden_indice`.

## Caveats conocidos

- **27 sesiones sin órden del día** en el índice oficial: se conservan con
  `agenda_items: []`.
- **1 sesión sin fecha** publicada (acta 93, período 2018-2021): `fecha: null`.
- **Enlaces PDF rotos** en el servidor del ayuntamiento para parte de 2013–2014
  (rutas `portal2014`). Se conservan tal cual.
- **Los PDF son escaneos sin capa de texto** (`docs/a3-spike.md`): el texto buscable
  proviene únicamente del índice HTML, es decir, del **órden del día**, no del
  contenido íntegro de las actas ni del sentido de las votaciones.
- **La numeración de la fuente a veces salta** (acta 76 de 2017 va de VI a VIII). Se
  respeta el salto; no se renumera.
- **Un período vacío se completó a partir de la fecha de sesión** — la única inferencia
  del pipeline, documentada en `docs/metodologia.md` §3.3.

## Licencias — posición actual (provisional)

⚠️ **Sujeto a X1.** Los Términos y Condiciones del portal restringen la reproducción y
comunicación pública de sus contenidos; ver `docs/x1-terminos-legal.md`. Mientras eso
se resuelve, la posición es deliberadamente conservadora:

- **Código:** MIT. Es nuestro.
- **Compilación y estructura** (el trabajo de extracción, normalización y organización):
  CC BY 4.0.
- **Texto oficial de los órdenes del día:** contenido del Ayuntamiento de Colima. Se
  atribuye y se enlaza al original; **no pretendemos licenciarlo**.
