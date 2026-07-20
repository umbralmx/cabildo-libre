# SOURCE.md — data/actas.json

- **Origen:** https://www.colima.gob.mx/portal2016/actas-de-cabildo/ (índice HTML de
  actas de cabildo del Ayuntamiento de Colima; texto del órden del día + enlaces PDF).
- **Transformación:** `scraper/scrape_colima.py` — sin ediciones manuales; cada registro
  es reproducible desde el índice.
- **Primera descarga:** 2026-07-19. Se actualiza automáticamente vía GitHub Actions
  (`.github/workflows/actualizar.yml`); el campo `generado` del JSON indica la corrida.
- **Licencia de esta redistribución:** CC BY 4.0. La información original es pública,
  generada por el Ayuntamiento de Colima.
- **Caveats conocidos:**
  - 27 sesiones sin órden del día en el índice oficial (se conservan con agenda vacía).
  - 1 sesión sin fecha en el índice (acta 93, período 2018-2021).
  - Enlaces PDF de 2013–2014 parcialmente rotos en el servidor del ayuntamiento.
  - Los PDF son escaneos sin texto (ver `docs/a3-spike.md`); el texto buscable
    proviene únicamente del índice HTML.
  - El índice duplicaba 4 sesiones; el scraper las deduplica (ver
    `split_agenda_items` y el bloque de dedupe en el scraper para las reglas).
