#!/usr/bin/env python3
"""Limpieza determinista del texto OCR — sin modelo, sin inventar.

El OCR crudo de Tesseract trae basura estructural: el membrete del acta se cuela
a mitad de página en cada salto ("ACTA DE CABILDO / H. AYUNTAMIENTO DE COLIMA /
Administración 2024-2027"), corridas de guiones e iguales ("----====--", "= = ="),
líneas partidas a la mitad y espacios de sobra. Esto ensucia tanto los fragmentos
de búsqueda que ve el lector como el texto que recibe el resumidor.

`limpiar()` quita **sólo** esa basura estructural y refluye párrafos. **Nunca
adivina ni reescribe palabras**: un OCR mal leído se queda como está (corregirlo
sería inventar registro público, justo lo que la regla del proyecto prohíbe). El
texto crudo se conserva intacto como evidencia; esto es una capa derivada.

Uso: `from limpieza import limpiar` — consumido por build_site_index (búsqueda) y
por summarize_colima (entrada al modelo). Se aplica al leer, no re-procesa el OCR.
"""

from __future__ import annotations

import re
import unicodedata


def _solo_letras(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z ]", "", s.lower()).strip()


# Fragmentos de membrete que se cuelan del encabezado/escudo en los saltos de
# página. Se comparan contra la línea reducida a letras, y sólo en líneas cortas
# (una línea de párrafo real no es únicamente "DE COLIMA").
_MEMBRETE = {
    "acta de cabildo", "ayuntamiento de colima", "h ayuntamiento de colima",
    "de colima", "colima", "gobierno municipal", "estados unidos mexicanos",
}
_MEMBRETE_RE = re.compile(r"administraci\w*\s*20\d\d\s*[-–—]?\s*20\d\d", re.I)

# Corridas de separadores, con o sin espacios: "----", "= = =", "—··—", ">>>".
_SEP_RUN = re.compile(r"(?:[-=_—–·•>«»|]\s?){3,}")
# Símbolos sueltos al inicio/fin de línea (no letras/dígitos/puntuación de frase).
_BORDE_IZQ = re.compile(r"^[\s\-=_—–·•>«»|\]\[)(]+")
_BORDE_DER = re.compile(r"[\s\-=_—–·•>«»|\]\[(]+$")


def _es_membrete(linea: str) -> bool:
    s = linea.strip()
    if not s:
        return False
    if re.fullmatch(r"\d{1,3}", s):           # línea que es sólo un número de página
        return True
    if _MEMBRETE_RE.search(s) and len(s) < 40:
        return True
    return _solo_letras(s) in _MEMBRETE and len(s) < 30


def limpiar(texto: str) -> str:
    # 1) por línea: quitar corridas de separadores, membrete y bordes de símbolos.
    lineas: list[str] = []
    for cruda in texto.split("\n"):
        linea = _SEP_RUN.sub(" ", cruda)
        linea = re.sub(r"[ \t]+", " ", linea).strip()
        if not linea:
            lineas.append("")
            continue
        if _es_membrete(linea):
            continue
        linea = _BORDE_DER.sub("", _BORDE_IZQ.sub("", linea)).strip()
        if linea:
            lineas.append(linea)
    texto = "\n".join(lineas)

    # 2) unir palabras partidas por guión al final de línea: "pala-\nbra" -> "palabra".
    texto = re.sub(r"(\w)[-–]\s*\n\s*(\w)", r"\1\2", texto)

    # 3) reflujo conservador: pegar una línea a la anterior cuando la anterior no
    #    cierra en puntuación de frase y ésta empieza en minúscula (es continuación).
    fuera: list[str] = []
    for ln in texto.split("\n"):
        if fuera and fuera[-1] and ln[:1].islower() and not re.search(r"[.:;!?]$", fuera[-1]):
            fuera[-1] = f"{fuera[-1]} {ln}"
        else:
            fuera.append(ln)
    texto = "\n".join(fuera)

    # 4) colapsar espacios y líneas en blanco de sobra.
    texto = re.sub(r"[ \t]{2,}", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


if __name__ == "__main__":  # pequeño uso manual: limpieza.py data/ocr/<id>.json
    import json
    import sys
    from pathlib import Path

    src = Path(sys.argv[1])
    d = json.loads(src.read_text(encoding="utf-8"))
    print(limpiar(d["texto_completo"]))
