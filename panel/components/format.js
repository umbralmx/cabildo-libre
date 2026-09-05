/**
 * Modo, formato numérico y etiquetas del término.
 *
 * Aquí no se escribe ningún color: los tokens salen de `tokensFor(MODE)`.
 */
import {tokensFor} from "@umbralmx/umbral-plot/tokens";

/*
 * Modo instrumento (oscuro).
 *
 * Es lo que la tabla de superficies de la guía asigna a un tablero. El
 * buscador y la metodología viven en `site/` y siguen en laboratorio: son
 * lectura y documento, no tablero. Cambiar esta constante y el `data-mode`
 * del documento mueve todo el sistema de color a la vez (UMB-COL-011).
 */
export const MODE = "instrumento";
export const T = tokensFor(MODE);

const nf = new Intl.NumberFormat("es-MX");
export const fmt = (n) => (n == null ? "sin dato" : nf.format(n));
export const fmtPct = (x, d = 0) => (x == null ? "sin dato" : `${(x * 100).toFixed(d)}%`);

/** Pesos completos. Una cifra de dinero público abreviada pierde su sentido. */
export const fmtMXN = (v) => (v == null ? "sin cifra" : "$" + nf.format(Math.round(v)));

/**
 * Pesos abreviados, sólo para una etiqueta estrecha de eje.
 * Nunca «MM»: a unos les dice *millones* y a otros *mil millones*, y ésa es
 * justo la ambigüedad que una cifra de dinero no puede permitirse.
 */
export function fmtMXNCorto(v) {
  if (v == null) return "—";
  const a = Math.abs(v);
  if (a >= 1e6) return `$${nf.format(Math.round(v / 1e6))}M`;
  if (a >= 1e3) return `$${Math.round(v / 1e3)}k`;
  return "$" + nf.format(v);
}

const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
export function fmtFecha(iso) {
  if (!iso) return "sin fecha";
  const [y, m, d] = iso.split("-");
  return `${Number(d)} ${MESES[Number(m) - 1]} ${y}`;
}

export const CATEGORIA_ES = {
  obra_publica: "Obra pública", licencia: "Licencias y permisos",
  fraccionamiento: "Fraccionamientos", presupuesto_finanzas: "Presupuesto y finanzas",
  nombramiento: "Nombramientos", convenio: "Convenios",
  reglamento_normativo: "Reglamentos", patrimonio: "Patrimonio",
  tramite: "Trámite interno", otro: "Otro"
};

export const SENTIDO_ES = {
  aprobado: "Aprobado", rechazado: "Rechazado", aplazado: "Aplazado",
  retirado: "Retirado", no_determinable: "Sin resultado legible"
};

/* ── CSV ────────────────────────────────────────────────────────────── */

function toCSV(rows, columns) {
  const cols = columns ?? Object.keys(rows[0] ?? {});
  const esc = (v) => {
    if (v == null) return "";
    const s = String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return [cols.join(","), ...rows.map((r) => cols.map((c) => esc(r[c])).join(","))].join("\n");
}

/** El CSV de cada gráfica (UMB-A11Y-004). */
export function csvButton({rows, columns, filename, label = "Descargar CSV"}) {
  const a = document.createElement("a");
  a.className = "u-btn";
  a.href = "#";
  a.textContent = label;
  // Un <a download> con href de marcador no descarga por sí solo: el clic
  // arma el archivo y lo entrega con un enlace de usar y tirar.
  a.addEventListener("click", (e) => {
    e.preventDefault();
    const url = URL.createObjectURL(
      new Blob([toCSV(rows, columns)], {type: "text/csv;charset=utf-8"})
    );
    const tmp = document.createElement("a");
    tmp.href = url;
    tmp.download = filename;
    document.body.append(tmp);
    tmp.click();
    tmp.remove();
    // Revocar en el mismo turno cancela la descarga en algunos navegadores.
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  return a;
}
