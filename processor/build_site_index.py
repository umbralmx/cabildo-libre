#!/usr/bin/env python3
"""Fase 2, etapa 3 — compila lo procesado en lo que el sitio carga.

Convierte `data/summaries/*.json` y `data/ocr/*.json` en lo que se sirve bajo `site/`:

  - `site/summaries.json` — pequeño, se carga siempre. Cuelga un resumen en lenguaje
    llano y un `sentido` de cada punto del órden del día que lo tenga.
  - `site/fulltext-index.json` — el índice de búsqueda: token → actas que lo contienen.
    Se carga una sola vez, en la primera búsqueda de texto completo.
  - `site/fulltext/<id>.json` — el texto OCR limpio de **una** acta. Se pide sólo para
    las actas que el índice señala como candidatas.

## Por qué existe el índice

Todo el corpus era un solo `site/fulltext.json` que se cargaba entero en la primera
búsqueda: **10.9 MB** para las 78 actas de un término, y faltan cuatro términos. La
búsqueda es el objetivo nº 1 del proyecto —«la espina dorsal»— y era lo más pesado del
sitio.

El índice pesa **~1.0 MB** y el 54 % de sus tokens aparece en una sola acta: el ruido del
OCR alarga el vocabulario y acorta las listas de postings, que aquí juega a favor. Una
búsqueda cuesta ahora el índice más las dos o tres actas que de verdad coinciden.

## Por qué los resultados no cambian

El índice **acota, no decide**. Devuelve un *superconjunto* de candidatas: una consulta
por prefijo une los postings de todos los tokens que empiezan igual, y una consulta de
frase no puede comprobar adyacencia desde los postings. Sobre el texto de cada candidata
corre después **el mismo regex de siempre**, así que los conteos, los fragmentos y el
resaltado son idénticos a los que producía el archivo monolítico.

De ahí que el único modo de fallo posible sea un **falso negativo**: un acta que coincide
y que el índice no propuso. Eso sólo puede ocurrir si al índice le falta un posting, y esa
es una invariante estructural que `processor/verificar.py` comprueba en cada corrida
(`indice_completo`). Los falsos positivos son inofensivos: el regex los descarta.

`fold` y `TOKEN` son espejo de `fold()` y de `\\b<token>[a-z0-9]*` en `site/app.js`. Si
dejan de serlo, el índice puede perder un acta que el navegador sí habría encontrado — por
eso están documentados aquí y comprobados allá.

## Lo que este diseño NO mejora, medido

Una consulta **entre comillas** (frase exacta) no se puede acotar bien: los postings no
saben de adyacencia, así que `"voto de calidad"` propone las 65 actas que contienen las tres
palabras por separado, y el regex se queda con 4. En esa consulta se piden 65 actas.

Se evaluó un índice de bigramas para arreglarlo y **se descartó con números**: el completo
pesa 6.46 MB y uno restringido a pares de palabras comunes, 2.72 MB — más que el índice
entero, para un caso que además no siempre tiene arreglo (`"orden del día"` y `"lista de
asistencia"` aparecen de verdad en las 78 actas, así que 78 candidatas es la respuesta
correcta, no un fallo del índice).

El balance honesto es este: el monolito descargaba **10.9 MB en la primera búsqueda,
siempre y buscara lo que buscara**. Aquí la primera búsqueda cuesta 1.03 MB más las actas
que coinciden —medido en el navegador: 1.46 MB para «carsol»— y cada acta se pide **una
sola vez** en toda la sesión. El peor caso acumulado se acerca al tamaño del corpus, pero
sólo se llega a él cuando la respuesta de verdad es «casi todas las actas».

Los tres archivos se escriben siempre (vacíos si aún no hay nada procesado) para que el
`fetch` del sitio nunca reciba un 404. Corre después de las etapas de OCR y de resumen;
está cableado en `procesar.yml`.

Uso: python3 processor/build_site_index.py
"""

from __future__ import annotations

import datetime
import json
import re
import shutil
import unicodedata
from pathlib import Path

from limpieza import limpiar

ROOT = Path(__file__).resolve().parent.parent
OCR_DIR = ROOT / "data" / "ocr"
SUMMARY_DIR = ROOT / "data" / "summaries"
SITE = ROOT / "site"
FT_DIR = SITE / "fulltext"


def build_summaries() -> dict:
    resumenes = {}
    for f in sorted(SUMMARY_DIR.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        resumenes[d["id"]] = {
            "modelo": d["modelo"],
            "sesion": d.get("resumen_sesion", ""),
            "puntos": {str(p["n"]): {"resumen": p["resumen"], "sentido": p["sentido"]}
                       for p in d["puntos"] if p["resumen"]},
        }
    return {
        "generado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "resumenes": resumenes,
    }


def fold(s: str) -> str:
    """Espejo de `fold()` en app.js — NFD, primer codepoint, minúscula.

    Tiene que seguir siendo un espejo. Si pliega un carácter distinto de como lo
    pliega el navegador, el índice puede perder un acta que el regex del sitio sí
    habría encontrado, y una búsqueda pierde un resultado en silencio en vez de
    fallar a la vista.
    """
    return "".join(unicodedata.normalize("NFD", ch)[0].lower() for ch in s)


# `\b` en JS considera [A-Za-z0-9_] como caracteres de palabra, y app.js busca
# `\b<token>[a-z0-9]*`. Partir también en `_` produce *más* tokens de los que el
# navegador trataría como inicio de palabra: candidatas de más, nunca de menos, y
# el regex descarta las sobrantes.
TOKEN = re.compile(r"[a-z0-9]+")


def tokens_de(texto: str) -> set[str]:
    return set(TOKEN.findall(fold(texto)))


def build_fulltext() -> tuple[dict[str, str], dict]:
    """El texto limpio de cada acta, y el índice invertido sobre él.

    Sirve el texto **limpio** (membrete y corridas de separadores fuera, párrafos
    refluidos) para que los fragmentos de búsqueda se lean bien. El OCR crudo se
    queda en `data/ocr/` como evidencia; la limpieza es determinista, nunca una
    reescritura del modelo.
    """
    textos: dict[str, str] = {}
    for f in sorted(OCR_DIR.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        textos[d["id"]] = limpiar(d["texto_completo"])

    # Los postings son índices dentro de `actas`, no ids: un id cuesta ~14 bytes
    # por aparición y hay más de 200 000 apariciones.
    ids = sorted(textos)
    posicion = {a: i for i, a in enumerate(ids)}
    indice: dict[str, list[int]] = {}
    for acta_id, texto in textos.items():
        i = posicion[acta_id]
        for tok in tokens_de(texto):
            indice.setdefault(tok, []).append(i)

    return textos, {
        "generado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "motor": "tesseract-spa",
        "actas": ids,
        # Ordenado para que el sitio pueda buscar por rango de prefijo con
        # búsqueda binaria en vez de recorrer 34 000 tokens en cada tecla.
        "tokens": {t: sorted(v) for t, v in sorted(indice.items())},
    }


def main() -> None:
    SITE.mkdir(parents=True, exist_ok=True)

    summaries = build_summaries()
    (SITE / "summaries.json").write_text(
        json.dumps(summaries, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    textos, indice = build_fulltext()

    # Se reconstruye desde cero: un acta re-OCR'd con un id corregido dejaría si no
    # su archivo viejo ahí, huérfano y todavía consultable.
    if FT_DIR.exists():
        shutil.rmtree(FT_DIR)
    FT_DIR.mkdir(parents=True, exist_ok=True)
    for acta_id, texto in textos.items():
        (FT_DIR / f"{acta_id}.json").write_text(
            json.dumps({"id": acta_id, "texto": texto}, ensure_ascii=False,
                       separators=(",", ":")), encoding="utf-8")

    (SITE / "fulltext-index.json").write_text(
        json.dumps(indice, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # El monolito que esto sustituye. Si se queda, son 10.9 MB de texto que ya no
    # lee nadie y que Pages sigue empaquetando en cada despliegue.
    (SITE / "fulltext.json").unlink(missing_ok=True)

    n_res = len(summaries["resumenes"])
    idx_mb = (SITE / "fulltext-index.json").stat().st_size / 1e6
    txt_mb = sum(f.stat().st_size for f in FT_DIR.glob("*.json")) / 1e6
    print(f"summaries.json:      {n_res} actas con resúmenes")
    print(f"fulltext-index.json: {len(indice['tokens']):,} tokens ({idx_mb:.2f} MB) — "
          f"lo único que baja una búsqueda")
    print(f"fulltext/:           {len(textos)} actas ({txt_mb:.1f} MB en total; "
          f"se piden sólo las que el índice señala)")


if __name__ == "__main__":
    main()
