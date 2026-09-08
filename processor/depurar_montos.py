#!/usr/bin/env python3
"""Quita de los resúmenes ya escritos los montos que su acta no contiene.

`summarize_colima.py` ya trae el guard, pero sólo actúa cuando un acta se
vuelve a resumir. Este script aplica **la misma regla** a lo que ya está en
`data/summaries/`, sin llamar al modelo: es determinista, no cuesta nada y no
mueve ninguna otra cifra. Volver a resumir habría costado dinero y, según la
bitácora, mueve ~1 % de los puntos en ambas direcciones sin tocar una línea de
código; para quitar dos cifras inventadas eso es un precio absurdo.

Uso:
    python3 processor/depurar_montos.py --dry-run   # sólo dice qué quitaría
    python3 processor/depurar_montos.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUMMARY_DIR = ROOT / "data" / "summaries"
OCR_DIR = ROOT / "data" / "ocr"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tocados = quitados = 0
    for p in sorted(SUMMARY_DIR.glob("*.json")):
        ocr_p = OCR_DIR / p.name
        if not ocr_p.exists():
            continue
        digitos = re.sub(r"\D", "", json.loads(ocr_p.read_text()).get("texto_completo", ""))
        d = json.loads(p.read_text())
        fuera: list[str] = []
        for pt in d.get("puntos", []):
            conservados = []
            for m in pt.get("montos") or []:
                nums = re.findall(r"\d[\d,\.\s]*\d|\d", m.get("texto") or "")
                cifra = re.sub(r"\D", "", max(nums, key=len)) if nums else ""
                if len(cifra) >= 4 and cifra not in digitos:
                    fuera.append(f"punto {pt.get('n')}: {m.get('texto')}")
                    continue
                conservados.append(m)
            pt["montos"] = conservados
        if not fuera:
            continue
        tocados += 1
        quitados += len(fuera)
        print(f"acta {d.get('no_acta')}:")
        for f in fuera:
            print(f"  − {f}")
        # Lo descartado se registra en el propio acta: una cifra que se cae se
        # reporta, no se desvanece.
        d["montos_descartados"] = sorted(set(d.get("montos_descartados", []) + fuera))
        if not args.dry_run:
            p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    verbo = "se quitarían" if args.dry_run else "quitados"
    print(f"\n{quitados} monto(s) {verbo} en {tocados} acta(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
