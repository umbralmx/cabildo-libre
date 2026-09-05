#!/usr/bin/env python3
"""Puerta de marca — comprueba que la interfaz cumpla el sistema Umbral.

`verificar.py` pregunta si una cifra es cierta. Éste pregunta otra cosa: si lo
publicado sigue las reglas del sistema de diseño que el proyecto dice seguir.

Son preguntas distintas y ninguna cubre a la otra. El linter del propio sistema
(`skills/umbral-brand/scripts/lint.py`, en umbral-style-guide) ya revisa la capa
mecánica —hexes a mano, radios, sombras— y pasa limpio. Lo que no puede ver es
el **contrato del marco de gráfica**, porque vive en la prosa y en el JS que la
genera. Eso es justo lo que cambió en la versión 2.0.0 del sistema:

- El subtítulo dice **cómo está construida** la cifra: la transformación, la
  unidad, el alcance y el periodo. Antes era `geografía · periodo · unidad`, que
  no nombraba ninguna transformación. Una suma acumulada y un total anual dibujan
  curvas distintas con los mismos datos, y el subtítulo viejo no distinguía.
- La línea de fuente tiene **dos lados**: de dónde salió el dato y cuándo se
  consultó a la izquierda, el sitio a la derecha. Ya no lleva ni la licencia ni
  la etiqueta de instantánea: ésas se mudaron a la página. Cinco campos en una
  línea no sobrevivían a una tarjeta social ni a una diapositiva.

Además vigila la deriva de tokens. El `assets/tokens.css` de la raíz llevaba la
versión 1.0 —con `caption` en #9AA19B, 2.37:1, el peor fallo de contraste que
midió la auditoría— mientras el sitio ya servía la corregida. Nadie lo notó
porque las dos copias no se comparaban con nada.

No llama a ningún modelo, no abre un navegador y no necesita dependencias: sólo
lee los archivos que se van a publicar. Un navegador da falsos negativos —durante
esta migración devolvió estilos vacíos para reglas que sí existían— y una puerta
en tiempo de construcción no tiene esa falla.

Severidades:
  ERROR  — bloquea la publicación. Lo publicado incumpliría una regla `error`.
  AVISO  — se reporta y no bloquea. Necesita criterio humano.

Uso:
    python3 processor/verificar_marca.py
    python3 processor/verificar_marca.py --guia /ruta/a/umbral-style-guide
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
SITIO = "umbral.org.mx"

# Frame.warnings() en @umbralmx/umbral-plot rechaza un subtítulo que no nombre
# ninguna transformación. Se replica aquí, con los términos que usa el panel.
TRANSFORMACION = re.compile(
    r"acumulad|total|tasa|promedio|mediana|cambio|porcentaje|suma|proporci|"
    r"distribuci|conteo|monto",
    re.I,
)
PERIODO = re.compile(r"\d{4}")


class Hallazgo:
    def __init__(self, check: str, severidad: str, mensaje: str, detalle=None):
        self.check, self.severidad = check, severidad
        self.mensaje, self.detalle = mensaje, detalle or []


def _lee(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def dominio() -> list[Hallazgo]:
    """El sistema publica en umbral.org.mx. `umbral.mx` es un dominio que el
    laboratorio no usa, y el repo lo citaba en doce lugares."""
    malos = []
    for p in sorted(SITE.glob("*.html")) + sorted(SITE.glob("*.js")) + [SITE / "styles.css"]:
        for i, linea in enumerate(_lee(p).splitlines(), 1):
            if re.search(r"umbral\.mx(?!\w)", linea.replace(SITIO, "")):
                malos.append(f"{p.name}:{i}")
    if malos:
        return [Hallazgo("dominio", "ERROR",
                         f"{len(malos)} referencia(s) a umbral.mx en vez de {SITIO}", malos)]
    return []


def linea_de_fuente() -> list[Hallazgo]:
    """UMB-CHT-003 — dos lados, sin licencia y sin etiqueta de instantánea."""
    out: list[Hallazgo] = []
    for p in sorted(SITE.glob("*.html")):
        html = _lee(p)
        for bloque in re.findall(r'<(?:p|figcaption)[^>]*class="fig-src[^"]*"[^>]*>(.*?)</(?:p|figcaption)>',
                                 html, re.S):
            texto = re.sub(r"<[^>]+>", "", bloque)
            texto = " ".join(texto.split())
            if "fig-src-origen" not in bloque or "fig-src-sitio" not in bloque:
                out.append(Hallazgo("linea-de-fuente", "ERROR",
                                    f"{p.name}: línea de fuente sin dos lados", [texto[:90]]))
                continue
            if not texto.startswith("Fuente: "):
                out.append(Hallazgo("linea-de-fuente", "ERROR",
                                    f"{p.name}: no abre con «Fuente: »", [texto[:90]]))
            if "Elaboración propia" not in texto:
                out.append(Hallazgo("linea-de-fuente", "AVISO",
                                    f"{p.name}: no dice «Elaboración propia con datos de …»",
                                    [texto[:90]]))
            if re.search(r"CC BY|licencia|MIT", texto, re.I):
                out.append(Hallazgo("linea-de-fuente", "ERROR",
                                    f"{p.name}: la licencia sigue en la gráfica (UMB-DAT-004)",
                                    [texto[:90]]))
    return out


def marco_generado() -> list[Hallazgo]:
    """Las ocho gráficas del panel se construyen en JS: se revisa la fuente."""
    js = _lee(SITE / "panel.js")
    out: list[Hallazgo] = []

    if f"const SITIO = '{SITIO}'" not in js:
        out.append(Hallazgo("marco", "ERROR", f"panel.js no fija el sitio en {SITIO}"))
    if "Consulta realizada el" not in js:
        out.append(Hallazgo("marco", "ERROR",
                            "el marco no escribe la fecha de consulta (UMB-CHT-003)"))
    if "CONSULTADO = (d.generado" not in js:
        out.append(Hallazgo("marco", "AVISO",
                            "la fecha de consulta no se lee del payload; puede quedar obsoleta"))

    fuentes = re.findall(r"fuente:\s*'([^']*)'", js)
    for f in fuentes:
        if f.startswith("Fuente:"):
            out.append(Hallazgo("marco", "ERROR",
                                "el llamador repite «Fuente:»; el marco ya lo escribe", [f[:70]]))
        if not f.startswith("Elaboración propia"):
            out.append(Hallazgo("marco", "AVISO",
                                "la fuente no abre con «Elaboración propia»", [f[:70]]))
    if len(fuentes) < 8:
        out.append(Hallazgo("marco", "AVISO",
                            f"se esperaban 8 gráficas con fuente, se hallaron {len(fuentes)}"))

    # UMB-CHT-002 — cada subtítulo nombra una transformación y un periodo.
    for m in re.finditer(r"subtitulo:\s*(.*?)(?:\n\s*fuente:|\n\s*\}\))", js, re.S):
        cuerpo = m.group(1)
        plano = " ".join(re.findall(r"[`'\"]([^`'\"]*)[`'\"]", cuerpo))
        if not TRANSFORMACION.search(plano):
            out.append(Hallazgo("marco", "ERROR",
                                "subtítulo sin transformación nombrada (UMB-CHT-002)",
                                [plano[:80]]))
        # El periodo puede venir interpolado: `${TERMINO}` o una fecha real del
        # payload. Exigir un literal de cuatro dígitos obligaría a escribir un
        # subtítulo peor —«2024-2027» en vez de «1 oct 2024 a 14 ago 2026»—, así
        # que la comprobación acepta la interpolación que sí produce un periodo.
        interpolado = "TERMINO" in cuerpo or "fecha" in cuerpo or "fmtFecha" in cuerpo
        if not PERIODO.search(plano) and not interpolado:
            out.append(Hallazgo("marco", "ERROR",
                                "subtítulo sin periodo (UMB-CHT-002)", [plano[:80]]))
    return out


def etiquetas_en_minuscula() -> list[Hallazgo]:
    """UMB-LAY-006 — las etiquetas de sección van en mono y en minúsculas."""
    css = _lee(SITE / "styles.css")
    malas = [b.strip().splitlines()[0].strip()
             for b in re.findall(r"([^{}]+)\{[^}]*text-transform:\s*uppercase[^}]*\}", css)]
    if malas:
        return [Hallazgo("etiquetas", "ERROR",
                         f"{len(malas)} regla(s) siguen en versalitas (UMB-LAY-006)", malas)]
    return []


def licencia_en_pagina() -> list[Hallazgo]:
    """UMB-DAT-004 — si la gráfica ya no lleva la licencia, la página debe."""
    out = []
    for p in sorted(SITE.glob("*.html")):
        if "CC BY 4.0" not in _lee(p):
            out.append(Hallazgo("licencia", "ERROR",
                                f"{p.name} no declara la licencia en la página"))
    return out


def deriva_de_tokens(guia: Path | None) -> list[Hallazgo]:
    """Las dos copias de tokens.css deben ser la del sistema, byte a byte."""
    sitio, raiz = SITE / "assets" / "tokens.css", ROOT / "assets" / "tokens.css"
    out = []
    if _lee(sitio) != _lee(raiz):
        out.append(Hallazgo("tokens", "ERROR",
                            "assets/tokens.css y site/assets/tokens.css divergen"))
    if guia:
        canon = guia / "skills" / "umbral-brand" / "assets" / "tokens.css"
        if not canon.exists():
            out.append(Hallazgo("tokens", "AVISO", f"no se halló la guía en {canon}"))
        elif _lee(canon) != _lee(sitio):
            out.append(Hallazgo("tokens", "ERROR",
                                "los tokens del sitio no son los del sistema (deriva de versión)"))
    else:
        out.append(Hallazgo("tokens", "AVISO",
                            "sin --guia no se comprueba la deriva contra el sistema"))
    if not (SITE / "assets" / "components.css").exists():
        out.append(Hallazgo("tokens", "ERROR", "falta site/assets/components.css (capa de componentes)"))
    for p in sorted(SITE.glob("*.html")):
        if "assets/components.css" not in _lee(p):
            out.append(Hallazgo("tokens", "ERROR", f"{p.name} no carga components.css"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--guia", type=Path, default=None,
                    help="ruta al repo umbral-style-guide, para comprobar deriva de tokens")
    args = ap.parse_args()

    hallazgos: list[Hallazgo] = []
    hallazgos += dominio()
    hallazgos += linea_de_fuente()
    hallazgos += marco_generado()
    hallazgos += etiquetas_en_minuscula()
    hallazgos += licencia_en_pagina()
    hallazgos += deriva_de_tokens(args.guia)

    errores = [h for h in hallazgos if h.severidad == "ERROR"]
    avisos = [h for h in hallazgos if h.severidad == "AVISO"]

    for h in hallazgos:
        print(f"{h.severidad:5} [{h.check}] {h.mensaje}")
        for d in h.detalle[:6]:
            print(f"        · {d}")
        if len(h.detalle) > 6:
            print(f"        · … y {len(h.detalle) - 6} más")

    print(f"\n{len(errores)} error(es) · {len(avisos)} aviso(s)")
    if not hallazgos:
        print("conforme al sistema Umbral")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
