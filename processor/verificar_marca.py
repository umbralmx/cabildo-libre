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
PANEL = ROOT / "panel"
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
    """Las gráficas del panel se construyen en JS, así que se revisa la fuente.

    Desde que el panel se reconstruyó sobre Observable Framework, el encuadre
    vive en `panel/components/frame.js` y las llamadas en `panel/index.md`. La
    validación dura la hace `Frame` de @umbralmx/umbral-plot en tiempo de
    ejecución —sin fuente, lanza—; esto es la comprobación estática que corre
    antes, sin navegador.
    """
    frame_js = _lee(PANEL / "components" / "frame.js")
    pagina = _lee(PANEL / "index.md")
    out: list[Hallazgo] = []

    if not frame_js or not pagina:
        return [Hallazgo("marco", "ERROR", "no se encontró el panel en panel/")]

    # El encuadre delega en Frame, que es quien se niega a dibujar sin fuente.
    if "from \"@umbralmx/umbral-plot\"" not in frame_js:
        out.append(Hallazgo("marco", "ERROR",
                            "frame.js no usa el Frame del sistema; la validación de "
                            "UMB-CHT-001/002/003 quedaría sin hacer"))
    if "frame.sourceLine()" not in frame_js or "frame.siteLine()" not in frame_js:
        out.append(Hallazgo("marco", "ERROR",
                            "el pie no se arma con las dos mitades de Frame (UMB-CHT-003)"))
    if "UMB-A11Y-004" not in frame_js or "download" not in frame_js:
        out.append(Hallazgo("marco", "AVISO", "el encuadre no exige el CSV de cada gráfica"))
    if "ariaLabel()" not in frame_js:
        out.append(Hallazgo("marco", "ERROR",
                            "la figura no lleva el hallazgo como aria-label (UMB-A11Y-002)"))

    # La licencia y el corte bajaron al pie de página, fuera de la línea de
    # fuente (UMB-DAT-002, UMB-DAT-004).
    if "CC BY 4.0" not in frame_js:
        out.append(Hallazgo("marco", "AVISO",
                            "el encuadre no declara la licencia junto al CSV"))

    # La fecha de consulta se lee del payload, nunca escrita a mano.
    if "d.generado" not in pagina:
        out.append(Hallazgo("marco", "ERROR",
                            "la fecha de consulta no se lee de `generado`; puede quedar obsoleta"))

    # Cada llamada a chartFrame lleva su fuente y su subtítulo.
    llamadas = pagina.count("chartFrame({")
    if llamadas < 8:
        out.append(Hallazgo("marco", "AVISO",
                            f"se esperaban 8 gráficas encuadradas, se hallaron {llamadas}"))
    for f in re.findall(r"source:\s*\n?\s*[\"']([^\"']*)", pagina):
        if f.startswith("Fuente:"):
            out.append(Hallazgo("marco", "ERROR",
                                "el llamador repite «Fuente:»; el marco ya lo escribe", [f[:70]]))
        if not f.startswith("Elaboración propia"):
            out.append(Hallazgo("marco", "AVISO",
                                "la fuente no abre con «Elaboración propia»", [f[:70]]))

    # UMB-CHT-002 — cada subtítulo nombra una transformación y un periodo. Se
    # aceptan las interpoladas: `${TERMINO}` produce el periodo en pantalla.
    for m in re.finditer(r"subtitle:\s*(.*?)(?:\n\s*source:|\n\s*consultado:)", pagina, re.S):
        cuerpo = m.group(1)
        plano = " ".join(re.findall(r"[`\"']([^`\"']*)[`\"']", cuerpo))
        if not TRANSFORMACION.search(plano):
            out.append(Hallazgo("marco", "ERROR",
                                "subtítulo sin transformación nombrada (UMB-CHT-002)",
                                [plano[:80]]))
        if not PERIODO.search(plano) and "TERMINO" not in cuerpo and "fecha" not in cuerpo.lower():
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
        html = _lee(p)
        # panel.html quedó como redirección al panel de Framework; su licencia
        # la declara la página de destino, no el trampolín.
        if "http-equiv=\"refresh\"" in html:
            continue
        if "CC BY 4.0" not in html:
            out.append(Hallazgo("licencia", "ERROR",
                                f"{p.name} no declara la licencia en la página"))
    if "CC BY 4.0" not in _lee(PANEL / "index.md"):
        out.append(Hallazgo("licencia", "ERROR",
                            "el panel no declara la licencia en la página (UMB-DAT-004)"))
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


def modo_instrumento() -> list[Hallazgo]:
    """**Todo el instrumento va en modo instrumento**, no sólo el panel.

    Es una desviación deliberada de la tabla de superficies, que pone `web` en
    laboratorio; el porqué está en docs/diseno.md. Lo que la regla sí exige, y
    esto comprueba, es que el modo sea **uno solo por artefacto** y que lo fije
    el medio y no el `prefers-color-scheme` del lector (UMB-COL-011). Media
    superficie clara y media oscura es el defecto que la regla existe para
    evitar, y es exactamente lo que pasa si una página se queda atrás.

    El atributo tiene que venir en el HTML. Si lo pusiera el JavaScript, la
    página parpadearía en claro antes de oscurecerse.
    """
    out: list[Hallazgo] = []
    for p in sorted(SITE.glob("*.html")):
        html = _lee(p)
        if 'data-mode="instrumento"' not in html:
            out.append(Hallazgo("modo", "ERROR",
                                f"{p.name} no declara modo instrumento en su <html>"))
        if "umbral-isotype-light.svg" in html:
            out.append(Hallazgo("modo", "ERROR",
                                f"{p.name} usa el isotipo de fondo claro sobre fondo oscuro"))
        if "prefers-color-scheme" in html:
            out.append(Hallazgo("modo", "ERROR",
                                f"{p.name} deja el modo al sistema del lector (UMB-COL-011)"))
    if "prefers-color-scheme" in _lee(SITE / "styles.css"):
        out.append(Hallazgo("modo", "ERROR",
                            "styles.css empareja un tema claro y uno oscuro (UMB-COL-011)"))
    return out


def panel_instrumento(guia: Path | None) -> list[Hallazgo]:
    """El panel, además, es una app de Observable Framework: su modo vive en
    tres lugares y los tres tienen que coincidir."""
    out: list[Hallazgo] = []
    fmt_js = _lee(PANEL / "components" / "format.js")
    chrome = _lee(PANEL / "components" / "chrome.js")
    copia = _lee(ROOT / "scripts" / "copy-static.mjs")
    conf = _lee(ROOT / "observablehq.config.js")

    if not conf:
        return [Hallazgo("panel", "ERROR", "no existe observablehq.config.js")]

    if 'MODE = "instrumento"' not in fmt_js:
        out.append(Hallazgo("panel", "ERROR",
                            "components/format.js no declara MODE = instrumento (UMB-COL-011)"))
    if 'dataset.mode = "instrumento"' not in chrome:
        out.append(Hallazgo("panel", "ERROR",
                            "chrome.js no fija data-mode en preview; la página parpadearía en claro"))
    if 'data-mode="instrumento"' not in copia:
        out.append(Hallazgo("panel", "ERROR",
                            "copy-static.mjs no escribe data-mode en el HTML construido"))
    if 'lang="es"' not in copia:
        out.append(Hallazgo("panel", "ERROR",
                            "copy-static.mjs no escribe lang; Framework emite <html> sin idioma "
                            "(UMB-A11Y-001, el caso peor: ausente, no equivocado)"))

    # `style`, nunca `theme`: un tema de Framework deriva cuatro colores con
    # color-mix() y ninguno llega a la compuerta de contraste (UMB-COL-012).
    if re.search(r"^\s*theme:", conf, re.M):
        out.append(Hallazgo("panel", "ERROR",
                            "observablehq.config.js usa `theme`; debe usar `style` (UMB-COL-012)"))
    if "globalStylesheets: []" not in conf:
        out.append(Hallazgo("panel", "ERROR",
                            "globalStylesheets no está vacío; Framework cargaría fuentes de un CDN "
                            "(UMB-TYP-005)"))

    # El isotipo claro es el que se ve sobre fondo oscuro.
    if "umbral-isotype-dark.svg" not in chrome:
        out.append(Hallazgo("panel", "AVISO",
                            "chrome.js no usa el isotipo de modo oscuro sobre fondo instrumento"))

    # La hoja generada se copia, no se escribe. Si diverge de la del sistema,
    # alguien la editó a mano.
    gen = PANEL / "observable-framework-instrumento.css"
    if not gen.exists():
        out.append(Hallazgo("panel", "ERROR", "falta observable-framework-instrumento.css"))
    elif guia:
        canon = guia / "packages" / "umbral-plot" / "dist" / gen.name
        if canon.exists() and _lee(canon) != _lee(gen):
            out.append(Hallazgo("panel", "ERROR",
                                "observable-framework-instrumento.css fue editada a mano; "
                                "se reemplaza con la del sistema, no se edita"))
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
    hallazgos += modo_instrumento()
    hallazgos += panel_instrumento(args.guia)

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
