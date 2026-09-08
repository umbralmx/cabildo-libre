#!/usr/bin/env python3
"""Ensayo en seco de las funciones puras del resumidor, antes de gastar.

Existe por una corrida concreta: `descartar_montos_inventados` usaba `re` sin
que el módulo lo importara. El fallo no salta al importar —el nombre se resuelve
al ejecutar la función—, así que la corrida hizo las siete ventanas de la acta
34, pagó sus llamadas y se cayó al terminar, tirando el trabajo entero.

Un `py_compile` no lo habría visto. Un `import` tampoco. Sólo lo ve ejecutar la
función. Eso es lo que hace este script, contra un acta ya OCR'd del repo y sin
tocar la red, en menos de un segundo.

Uso:
    python3 processor/preflight.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "processor"))

import summarize_colima as sc  # noqa: E402


def main() -> int:
    # Se busca un acta que traiga alguna cifra larga: con la primera por orden
    # alfabético la prueba se saltaba sola y no comprobaba nada.
    texto, real = "", None
    for f in sorted((ROOT / "data" / "ocr").glob("*.json")):
        t = json.loads(f.read_text()).get("texto_completo", "")
        m = re.search(r"\d[\d,\.]{6,}\d", t)
        if m:
            texto, real = t, m
            break
    if real is None:
        print("preflight: ningún acta OCR'd trae una cifra larga; se omite")
        return 0

    # Se prueban las DOS direcciones: que tire la inventada y que respete la
    # real. Un guard que lo tira todo pasaría una prueba de una sola dirección
    # y borraría cada cifra del corpus.
    inventada = "9" * 12
    puntos = [{"n": 1, "montos": [
        {"texto": f"${inventada}", "valor_mxn": 1.0},
        {"texto": f"${real.group(0)}", "valor_mxn": 2.0},
    ]}]
    limpios, fuera = sc.descartar_montos_inventados(puntos, texto)
    quedan = [m["texto"] for m in limpios[0]["montos"]]
    if len(fuera) != 1 or len(quedan) != 1 or inventada in quedan[0]:
        print(f"preflight: el guard falló — descartó {fuera}, dejó {quedan}", file=sys.stderr)
        return 1

    # Las otras funciones puras del camino de escritura, sólo por ejecutarlas.
    sc._clean_montos([{"texto": "$1.00", "valor_mxn": 1.0}])
    sc.fusionar_puntos([[{"n": 1, "resumen": "x", "sentido": "aprobado"}]])

    print(f"preflight: ok — el guard tira la cifra ausente y conserva {quedan[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
