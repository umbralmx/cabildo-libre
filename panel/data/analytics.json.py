#!/usr/bin/env python3
"""Entrega el agregado del término al tablero.

El archivo lo produce `processor/build_analytics.py` y ya vive en `site/`,
commiteado, porque el buscador estático también lo lee. Aquí no se recalcula
nada: un cargador que volviera a agregar sería una segunda definición de cada
cifra, que es justo lo que la cadena de procedencia existe para evitar.

Si el archivo falta, este cargador falla y con él la construcción. Es
deliberado: un tablero que se publica vacío miente menos que uno que se
publica con las cifras del corte anterior, pero miente igual.
"""

import sys
from pathlib import Path

TERMINO = "2024-2027"
ROOT = Path(__file__).resolve().parents[2]
ORIGEN = ROOT / "site" / f"analytics-{TERMINO}.json"

if not ORIGEN.exists():
    sys.exit(
        f"no existe {ORIGEN.relative_to(ROOT)}. "
        "Corre processor/build_analytics.py antes de construir el panel."
    )

sys.stdout.write(ORIGEN.read_text(encoding="utf-8"))
