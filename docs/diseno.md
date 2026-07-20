# Diseño — aplicación del sistema Umbral a Actas Abiertas

Registro de cómo se aplicó el manual de marca (`assets/CLAUDE.md`) y
`assets/umbral-engineering.md` a este sitio, y de las decisiones que requirieron
interpretación. Última revisión: **2026-07-20**.

Modo: **laboratorio (light)**, que es el que corresponde a sitios web y reportes
según §8 del manual. No hay modo instrumento en este proyecto.

## Presupuesto de signal — la decisión de más criterio

La regla dice que `signal` se reserva para **el elemento más importante de cada vista**
y que nunca es decorativo. Aquí conviven varios usos, y esta es la lectura que los
justifica: **cada uso de signal marca identidad, una coincidencia, o un estado activo.
Ninguno es decoración.**

| Uso | Justificación |
|---|---|
| Guion bajo del wordmark `umbral_` | Parte de la especificación del logo (§5) |
| Acento del hero («Cabildo de Colima») | §8 concede explícitamente *un* acento de signal al hero de un sitio |
| Coincidencias de búsqueda (`<mark>`) | Son *el hallazgo*: el elemento más importante de la vista de resultados |
| Regla izquierda de la sesión abierta | Especificación de fila destacada (engineering §3) |
| Hover y focus | Especificación de componentes (engineering §3) |

Ajuste consciente: la regla de 4px de la sesión abierta se aplica **sólo al renglón de
resumen**, no a todo el bloque desplegado. Recorrer 800px de barra teal convertía un
marcador de estado en decoración — justo lo que la regla prohíbe.

## Tipografía

- **Space Grotesk 500** en h1, h2 y valores de estadística. Nunca 700 (§4 y lista de
  rechazo §9). Tracking `-0.02em` vía token.
- **IBM Plex Sans** en cuerpo, controles y texto de los puntos de agenda.
- **IBM Plex Mono** en fechas, etiquetas de campo, conteos, cifras y línea de fuente,
  con `tabular-nums` donde hay números que se comparan en columna.
- Escala respetada: h1 `clamp(40px, 5.5vw, 56px)` (rango 40–64), h2 de sección 24px
  (rango 22–26), cuerpo 16–17px con interlínea 1.55, etiquetas 13–14px, mono 12px.
- **Fuentes auto-hospedadas** (`site/assets/fonts/`, 12 archivos woff2, ~260 KB,
  subconjuntos latin y latin-ext para diacríticos del español). Sin dependencia de
  Google Fonts: el manual lo pide para productos que deben funcionar en redes
  gubernamentales o sin conexión.

## Color y forma

- Todos los colores salen de `assets/tokens.css`. **Ningún hex escrito a mano.**
- Sin gradientes, sin sombras, sin esquinas redondeadas (radio 0), sin botones píldora,
  sin negro ni blanco puros. Las reglas de 1px hacen el trabajo estructural.
- Escala de espaciado de 8px (`scale.unit` en tokens.json) en todo el layout.

## Composición

- Medida de texto máxima ~65ch en prosa; los puntos de agenda llegan a 72ch porque son
  texto administrativo denso donde una medida muy corta fragmenta la lectura.
- La línea de tiempo sigue la especificación de tabla: regla superior de 2px en `ink`
  por año, reglas de 1px entre sesiones, fechas en mono.
- Fila de estadísticas siguiendo la especificación de KPI: etiqueta en mono `caption`
  en versalitas, valor en Space Grotesk 500 a 32px. Responde al principio de voz «los
  números cargan el argumento» (§2): la primera cosa concreta que ve quien entra es
  636 sesiones y 6,992 puntos, no una promesa.

## Accesibilidad

- `lang="es"` para pronunciación correcta en lectores de pantalla.
- **Nada codificado sólo por color:** las coincidencias llevan color *más* peso 600
  *más* subrayado; los puntos procedimentales se distinguen por tono pero su texto
  completo siempre está presente y es igualmente buscable.
- Objetivos táctiles ≥44px en controles y renglones de sesión.
- `:focus-visible` con contorno en signal; `prefers-reduced-motion` respetado tanto en
  la animación de despliegue como en el desplazamiento suave.
- Contraste AA con los tokens del modo laboratorio.

## Voz

Español primero. Enunciados completos, sin signos de admiración, sin emoji, sin
palabras de bombo. La metodología nombra la fuente, el método y los vacíos; el estado
vacío de búsqueda explica *por qué* algo puede no aparecer (los PDF son escaneos) en
lugar de sólo decir «sin resultados».

## Desviaciones deliberadas del manual

1. **Sin conmutador ES/EN** en la navegación, aunque §7 lo incluye en el patrón de
   header. Es una herramienta municipal para residentes de Colima; no es un artefacto
   internacional. El manual pide «español primero, inglés para artefactos
   internacionales» — este no lo es.
2. **Sin «Proyectos»** en la navegación: este sitio es un proyecto, no el portal de
   umbral_. La navegación lleva a Datos, Metodología y la fuente oficial.
3. **Wordmark construido en HTML** en lugar de usar `umbral-lockup-light.svg`. El SVG
   del lockup trae el texto como `<text>` y, cargado como `<img>`, no accede a las
   fuentes auto-hospedadas: caería a una sans genérica. El isotipo (sin texto) sí se
   usa como SVG.

## Lista de verificación previa al lanzamiento

- [x] Modo correcto para el medio (laboratorio/light para sitio web)
- [x] Colores tomados de tokens, no escritos a mano
- [x] Display en Space Grotesk 500; cuerpo en Plex Sans; datos en Plex Mono
- [x] Español primero; fuente nombrada y enlazada
- [x] Nada de la lista de rechazo (§9)
- [x] Contraste AA, sin codificación sólo por color, foco visible, objetivos ≥44px
- [x] Vacíos de datos declarados en pantalla, no ocultos
- [ ] Licencia de datos definitiva — depende de X1 (`docs/x1-terminos-legal.md`)
