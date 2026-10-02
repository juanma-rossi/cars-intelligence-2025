# Guía Maestra: Dashboard Inmersivo en Power BI
### Inspirado en el estilo de Armand van Amersfoort — DAX + HTML/CSS/SVG + MCP + GitHub

> Objetivo del proyecto: construir, documentar y publicar un dashboard de portafolio que combine modelado analítico riguroso (DAX) con una capa visual "no convencional" (SVG/HTML) y un flujo de trabajo profesional versionado en GitHub, potenciado por Power BI MCP donde realmente aporta valor.

---

## 1. Selección del dataset

La clave no es "el dataset más popular de Kaggle", sino uno con **suficiente riqueza narrativa** (geografía, tiempo, jerarquía, un "héroe" visual — un piloto, un país, una canción) para que el esfuerzo en SVG tenga sentido. Aquí van 3 candidatos sólidos:

### 1.1 Formula 1 World Championship (1950–2020+)
**Kaggle:** `rohanrao/formula-1-world-championship-1950-2020`
- Por qué funciona: tiene pilotos, escuderías, circuitos, vueltas rápidas y resultados por temporada — es decir, jerarquía + tiempo + geografía en un solo dataset.
- Encaja perfecto con el estilo Armand: puedes construir un "mapa de circuito" en SVG, pines dinámicos por posición de parrilla, y tarjetas KPI animadas por piloto (podios, puntos, posición actual).
- Reto técnico interesante: normalizar resultados por temporada (esquema copo de nieve → estrella).

### 1.2 Global EV / Energía Renovable (Sostenibilidad)
**Kaggle:** ej. `patricklford/electric-vehicle-population-data` o cualquier dataset de adopción de EVs / mix energético por país (IEA/Our World in Data también republican estos datos en Kaggle).
- Por qué funciona: combina series temporales + geografía (mapas coropléticos) + storytelling de sostenibilidad, un tema con mucho tirón visual y de marca (verde, gradientes, iconografía).
- Encaja con el estilo Armand: KPI cards con "barras de progreso" hacia una meta (ej. % de flota eléctrica), iconos SVG animados de vehículos/baterías, paleta de color consistente tipo "corporate identity".

### 1.3 Spotify / Top Tracks & Audio Features
**Kaggle:** ej. `maharshipandya/-spotify-tracks-dataset` o "Top Spotify Songs" (actualizados con frecuencia).
- Por qué funciona: variables de audio (energy, valence, danceability, tempo) se prestan a gráficos radar/polares poco convencionales, y el dominio (música) permite integrar portadas de álbum como imágenes dentro de tarjetas SVG.
- Encaja con el estilo Armand: tarjetas de "ahora sonando" con carátula + halo de color dinámico según el género, transiciones tipo reproductor, uso de tipografía expresiva.

**Recomendación práctica:** si es tu primer proyecto de este tipo, empieza con **F1** o **Sostenibilidad/EV** — tienen jerarquías más claras para practicar modelado en estrella antes de meterte de lleno en SVG. Deja Spotify para una segunda iteración más "creativa".

---

## 2. Arquitectura del proyecto

Usa el formato **PBIP (Power BI Project) + TMDL**, no el `.pbix` binario clásico. PBIP guarda el reporte y el modelo semántico como carpetas de texto plano (JSON/TMDL), lo cual es indispensable para tener diffs legibles en Git — algo que un `.pbix` binario simplemente no permite.

Actívalo en Power BI Desktop: `Archivo > Opciones y configuración > Opciones > Características en versión preliminar > "Power BI Project (.pbip) save option"`.

### 2.1 Estructura de carpetas recomendada

```
powerbi-immersive-dashboard/
├── README.md                      # Portada del portafolio (screenshots, gif, storytelling)
├── LICENSE
├── .gitignore
├── .gitattributes                 # Para Git LFS si guardas binarios pesados
│
├── src/
│   ├── Dashboard.pbip             # Puntero del proyecto (lo abre Power BI Desktop)
│   ├── Dashboard.Report/          # Definición del reporte (PBIR: páginas, visuales, config)
│   │   └── definition/
│   └── Dashboard.SemanticModel/   # Modelo en TMDL (tablas, medidas, relaciones)
│       └── definition/
│           ├── tables/
│           ├── relationships.tmdl
│           └── model.tmdl
│
├── data/
│   ├── raw/                       # Datos originales de Kaggle (o link/script de descarga)
│   └── processed/                 # Datos limpios (Python/Power Query)
│
├── assets/
│   ├── svg/                       # Componentes SVG reutilizables (KPI cards, iconos)
│   ├── icons/
│   ├── fonts/
│   └── images/                    # Fondos, avatares, logos
│
├── themes/
│   └── theme.json                 # Tema de color/tipografía de Power BI
│
├── dax/
│   └── measures-catalog.md        # Catálogo documentado de medidas DAX (fuera del modelo)
│
├── scripts/
│   ├── data_prep.py               # Limpieza/ETL con Python
│   └── kaggle_download.py
│
├── docs/
│   ├── architecture.md
│   ├── screenshots/
│   └── demo.gif
│
└── .github/
    └── workflows/
        └── validate-tmdl.yml      # (opcional) valida sintaxis TMDL en cada PR
```

### 2.2 `.gitignore` esencial para PBIP

```gitignore
# Cachés y archivos temporales de Power BI
*.pbix.bak
.pbi/
*.tmp
~$*

# Si mantienes también un .pbix de respaldo (no recomendado como fuente de verdad)
# usa Git LFS en vez de ignorarlo:
# *.pbix filter=lfs diff=lfs merge=lfs -text

# Python
__pycache__/
*.pyc
.venv/

# Sistema
.DS_Store
Thumbs.db
```

Si por compatibilidad necesitas conservar también un `.pbix` (por ejemplo para compartir con alguien sin PBIP habilitado), trackéalo con **Git LFS**, nunca en Git plano:

```bash
git lfs install
git lfs track "*.pbix"
git add .gitattributes
```

---

## 3. Flujo de trabajo técnico

### 3.1 Power BI + MCP: qué existe hoy y dónde está el límite real

Esto es importante y quiero ser explícito porque hay mucho ruido en redes sobre "Power BI con IA":

**Lo que sí existe (y es oficial):**
- **Power BI MCP Server (remoto, en preview)** — Microsoft lo expone en `https://api.fabric.microsoft.com/v1/mcp/powerbi`. Permite a un cliente MCP (VS Code + GitHub Copilot, Claude Desktop, etc.) hacer preguntas en lenguaje natural sobre un **modelo semántico ya publicado**, generando y ejecutando DAX por debajo. Requiere que un admin de Fabric habilite la opción de tenant correspondiente y que tengas permiso "Build" sobre el modelo.
- **Power BI MCP Server (local, en preview)** — pensado para desarrollo de modelos semánticos (crear/editar tablas, medidas, relaciones vía lenguaje natural). Requiere VS Code o Node.js 20+, y hoy funciona mejor en Windows.
- **Opciones de comunidad** (no oficiales, útiles pero con más fricción): servidores MCP basados en el endpoint XMLA de Power BI Desktop (ej. `powerbi-mcp`), que permiten a Claude consultar el modelo abierto localmente, ejecutar DAX y leer el esquema — requieren Windows + Power BI Desktop abierto + `pythonnet`/`pyadomd`.

**La limitación explícita que debes conocer:** ningún servidor MCP de Power BI (oficial o comunitario) edita la **capa visual del reporte** — no genera tus SVG, no toca el canvas, no diseña layouts. MCP hoy vive en la capa de **modelo semántico y DAX**, no en la capa de diseño. Es una herramienta de productividad para modelado, no un generador de dashboards inmersivos.

**Cómo usarlo entonces en este proyecto (flujo recomendado):**
1. Usa el MCP local o el basado en XMLA para: validar medidas DAX recién creadas, pedirle a Claude que audite el modelo en busca de relaciones ambiguas, o generar variantes de una medida ("dame esta medida pero acumulada YTD").
2. Para la capa visual (SVG/HTML), trabaja en modo "código primero": pide a Claude (en este chat o en Claude Code) que te genere el DAX que produce el string SVG, y luego pega/valida ese resultado directamente en Power BI Desktop.
3. Configuración de ejemplo para Claude Desktop (servidor comunitario vía XMLA):

```json
{
  "mcpServers": {
    "powerbi": {
      "command": "python",
      "args": ["path/to/powerbi-mcp/server.py"],
      "env": {
        "PBI_XMLA_PORT": "auto-detect"
      }
    }
  }
}
```

> Si tu organización no ha habilitado el MCP remoto de Fabric, la alternativa realista es: modelar en PBIP/TMDL con ayuda de Claude Code para escribir/editar directamente los archivos `.tmdl` como texto, y usar Power BI Desktop solo para verificar visualmente.

### 3.2 DAX vs. HTML/CSS/SVG — cuándo usar cada uno

| Necesidad | Usa DAX | Usa SVG (vía medida) | Usa HTML/CSS |
|---|---|---|---|
| Cálculo de negocio (YoY, % del total, ranking) | ✅ Siempre | ❌ | ❌ |
| Icono o forma que cambia de color/tamaño según el dato | Calcula el valor/color en DAX | ✅ Renderiza el shape | ❌ |
| Barra de progreso, gauge o "mini-chart" custom | Calcula el % en DAX | ✅ Dibuja el rectángulo/arco | ❌ |
| Tarjeta KPI con tipografía rica, sombras, capas | Aporta el valor | ✅ (SVG con `foreignObject` para texto enriquecido) | Alternativa vía visual "HTML Content" |
| Tooltip narrativo con texto formateado, listas, links | Aporta los valores | ❌ | ✅ (visual custom "HTML Content" de AppSource) |
| Mapa de calor, pines dinámicos sobre una imagen | Calcula posición X/Y normalizada | ✅ (círculos/pines posicionados por variable) | ❌ |
| Visualización totalmente a medida (radar, sankey, custom) | Aporta los datos | Considera **Deneb** (visual basado en Vega-Lite) en vez de SVG a mano | — |

**Patrón clásico: medida DAX que devuelve un SVG como Data URI**, usada como campo "Imagen" en una tabla o tarjeta:

```dax
KPI Icono Semáforo =
VAR _valorActual = [Ventas Totales]
VAR _meta = [Meta de Ventas]
VAR _color =
    SWITCH(
        TRUE(),
        _valorActual >= _meta, "#00C48C",
        _valorActual >= _meta * 0.8, "#FFB020",
        "#FF5252"
    )
RETURN
    "data:image/svg+xml;utf8," &
    "<svg xmlns='http://www.w3.org/2000/svg' width='36' height='36'>" &
    "<circle cx='18' cy='18' r='16' fill='" & _color & "' opacity='0.9'/>" &
    "</svg>"
```

**Patrón: barra de progreso dinámica dentro de una tabla**

```dax
Barra Progreso SVG =
VAR pct = DIVIDE([Ventas Actuales], [Meta Ventas], 0)
VAR anchoTotal = 160
VAR anchoRelleno = MIN(pct, 1) * anchoTotal
RETURN
    "data:image/svg+xml;utf8," &
    "<svg xmlns='http://www.w3.org/2000/svg' width='" & anchoTotal & "' height='18'>" &
    "<rect width='" & anchoTotal & "' height='18' rx='6' fill='#2A2E37'/>" &
    "<rect width='" & anchoRelleno & "' height='18' rx='6' fill='#4C6FFF'/>" &
    "</svg>"
```

Para contenido **HTML/CSS real** (no solo SVG), la única vía nativa en Power BI es un **visual personalizado** que interprete HTML (por ejemplo el visual "HTML Content" de AppSource) o usar **Deneb**, que te da control tipo "código" (gramática Vega-Lite) sobre casi cualquier aspecto visual sin depender de SVG a mano. Si tu meta es "personalización visual avanzada" con el menor esfuerzo de mantenimiento, evalúa Deneb en paralelo a tus experimentos con SVG puro.

### 3.3 Versionado con Git/GitHub

```bash
# 1. Convertir el .pbix existente a PBIP desde Power BI Desktop
#    (Archivo > Guardar como > Power BI Project (*.pbip))

# 2. Inicializar el repo
cd powerbi-immersive-dashboard
git init
git add .
git commit -m "chore: initial PBIP project structure"

# 3. Crear el remoto y subir
git remote add origin https://github.com/tu-usuario/powerbi-immersive-dashboard.git
git branch -M main
git push -u origin main

# 4. Trabajar por features (una rama por fase o por componente visual)
git checkout -b feature/kpi-cards-svg
# ... cambios en Dashboard.Report y measures-catalog.md ...
git add .
git commit -m "feat(visual): tarjetas KPI animadas con SVG dinámico"
git push -u origin feature/kpi-cards-svg
# Abrir Pull Request en GitHub, revisar el diff de TMDL/PBIR (¡legible!) y hacer merge
```

Convenciones recomendadas:
- **Commits:** estilo [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `chore:`, `docs:`) — se ve muy profesional en un portafolio.
- **Ramas:** `main` (estable/publicable), `feature/<nombre>` por cada bloque funcional o visual.
- **Tags/releases:** etiqueta cada hito visible (`v0.1-modelo-listo`, `v1.0-portafolio`) para poder mostrar la evolución del proyecto en el README.

---

## 4. Roadmap por fases

| Fase | Objetivo | Herramientas | Duración estimada |
|---|---|---|---|
| **1. Setup & Fundación de Datos** | Elegir dataset, limpiar/transformar datos, crear repo con estructura PBIP | Kaggle, Python/Power Query, GitHub, VS Code | 3–5 días |
| **2. Modelado & DAX** | Diseñar esquema en estrella, relaciones, medidas base y avanzadas (time intelligence, ranking) | Power BI Desktop, DAX, MCP local (validación) | 5–7 días |
| **3. Diseño Visual & Sistema de Estilos** | Moodboard inspirado en Armand, paleta de color, tipografía, `theme.json`, wireframes de página | Figma/papel, Power BI Theme JSON | 4–6 días |
| **4. Desarrollo SVG/HTML Inmersivo** | Construir componentes: KPI cards animadas, pines dinámicos, barras/gauges custom, tooltips HTML | DAX, SVG, Deneb (opcional), VS Code | 8–10 días |
| **5. Interactividad & Integración MCP** | Bookmarks, drillthrough, botones de navegación, uso de MCP para QA de medidas, pruebas de rendimiento | Power BI Desktop, Performance Analyzer, Claude + MCP | 4–5 días |
| **6. Publicación & Portafolio** | README con GIF/capturas, publicar/embeber el reporte, post de LinkedIn, pulido final | GitHub, Power BI Service/Fabric, OBS/ScreenToGif | 2–3 días |

**Duración total estimada: 4–5 semanas** trabajando a ritmo de proyecto paralelo (no full-time).

---

## 5. Técnicas de Armand van Amersfoort y cómo replicarlas

Analizando su trabajo público (LinkedIn, artículos, comunidad Power BI Core Visuals), estos son los patrones más recurrentes y reproducibles:

### 5.1 Tarjetas KPI que "cobran vida" con SVG animado
En vez de una tarjeta estática, usa transiciones CSS dentro del SVG (con `<animate>` o `<style>` embebido) para que el número o el ícono tengan una entrada suave.

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60">
  <circle cx="30" cy="30" r="0" fill="#4C6FFF">
    <animate attributeName="r" from="0" to="26" dur="0.6s" fill="freeze" />
  </circle>
</svg>
```
*Replicarlo:* genera el SVG completo como string DAX (como en la sección 3.2), incluyendo el bloque `<style>` o `<animate>` inline — Power BI simplemente renderiza el data URI, así que cualquier SVG válido con animación CSS/SMIL funciona.

### 5.2 HTML y CSS incrustados dentro de SVG (`foreignObject`)
Para lograr tipografía rica (múltiples pesos, saltos de línea, iconos inline) dentro de una "tarjeta" SVG, se usa `<foreignObject>` para inyectar un `<div>` con CSS normal dentro del propio SVG.

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="80">
  <foreignObject width="200" height="80">
    <div xmlns="http://www.w3.org/1999/xhtml"
         style="font-family:Segoe UI; color:#fff; background:#1E2230; border-radius:12px; padding:10px;">
      <strong style="font-size:20px;">€ 128.4K</strong><br/>
      <span style="font-size:11px; opacity:0.7;">Ventas del mes</span>
    </div>
  </foreignObject>
</svg>
```
*Replicarlo:* esta es la técnica que permite "diseño web real" dentro de un visual de Power BI — trátala como tu bloque de construcción principal para tarjetas complejas.

### 5.3 Pines/hotspots dinámicos posicionados por datos
En vez de imágenes estáticas con puntos fijos, las coordenadas X/Y del pin se calculan a partir de los datos (ej. posición normalizada en un mapa de circuito, o coordenadas reales convertidas a un sistema de plano SVG).

```dax
Pin Piloto SVG =
VAR x = [PosicionX_Normalizada] * 500
VAR y = [PosicionY_Normalizada] * 300
VAR color = [ColorEscuderia]
RETURN
    "<circle cx='" & x & "' cy='" & y & "' r='6' fill='" & color & "' stroke='white' stroke-width='1.5'/>"
```
Estos fragmentos de círculo se concatenan (vía medida o vía `CONCATENATEX` sobre una tabla filtrada) dentro de un único SVG "lienzo" que contiene todos los pines activos según el filtro actual.

### 5.4 Capas de "mira aquí" — un solo elemento de foco visual
Un patrón simple pero efectivo: una sola forma o texto (no un layout completo) posicionado y rotado manualmente para dirigir la atención del usuario a un punto concreto ("Click aquí", una flecha, un círculo de énfasis). Al ser una sola capa, el rendimiento se mantiene alto.
*Replicarlo:* crea un shape/texto en Power BI, ajusta padding/rotación/alineación manualmente para "apuntar" a la zona relevante, y actívalo/desactívalo vía bookmark según el contexto.

### 5.5 Paletas de color y transparencia coherentes con marca
Contenedores con y sin color de fondo, jugando con transparencia y grises neutros para que los acentos de marca (o de tu dataset — ej. colores de escudería en F1) resalten sin saturar.
*Replicarlo:* define 2–3 grises base + 1–2 colores de acento en tu `theme.json`, y reutilízalos tanto en los shapes nativos como en los valores de `fill` dentro de tus SVG, para que todo se sienta parte de un mismo sistema.

---

## 6. Recursos de aprendizaje

**DAX**
- [SQLBI](https://www.sqlbi.com/) y [DAX Patterns](https://www.daxpatterns.com/) — la referencia técnica más rigurosa que existe.
- *The Definitive Guide to DAX* (Russo & Ferrari) — libro de cabecera para medidas avanzadas.

**Power BI general y rendimiento**
- Canal "Guy in a Cube" en YouTube — tutoriales prácticos y noticias de producto.
- [Microsoft Learn – Power BI](https://learn.microsoft.com/power-bi/) — documentación oficial, incluida la sección de Performance Analyzer.

**SVG/HTML inmersivo en Power BI**
- El propio canal de YouTube y LinkedIn de Armand van Amersfoort — sigue publicando ejemplos con código.
- Comunidad "Power BI Core Visuals" y blogs de la comunidad sobre "SVG measures in Power BI" (búscalos por ese término exacto para encontrar los posts más recientes).
- [Deneb](https://deneb-viz.github.io/) — documentación del visual basado en Vega-Lite, alternativa robusta a SVG a mano.

**PBIP / TMDL / Git**
- [Microsoft Learn – Power BI Projects (PBIP)](https://learn.microsoft.com/power-bi/developer/projects/projects-overview)
- [Pro Git (libro gratuito)](https://git-scm.com/book/en/v2)
- GitHub Skills (cursos interactivos oficiales de GitHub)

**Power BI MCP**
- [Microsoft Learn – Power BI MCP servers](https://learn.microsoft.com/power-bi/developer/mcp/)
- Documentación del Model Context Protocol en [modelcontextprotocol.io](https://modelcontextprotocol.io/)

---

## 7. Checklist final de verificación

- [ ] Dataset limpio, documentado y con script de descarga/transformación reproducible
- [ ] Modelo en esquema estrella, guardado en formato **PBIP + TMDL**
- [ ] Catálogo de medidas DAX documentado (`dax/measures-catalog.md`) con nombres consistentes y carpetas de visualización
- [ ] `theme.json` aplicado de forma consistente en todas las páginas
- [ ] Al menos 3 componentes SVG/HTML custom implementados y **dirigidos por datos** (no imágenes estáticas)
- [ ] Interactividad probada: bookmarks, drillthrough, tooltips personalizados
- [ ] Rendimiento verificado con Performance Analyzer (visuales SVG pesados no deben degradar el tiempo de carga)
- [ ] Si usaste MCP: documentado en el README qué tareas resolvió (modelado/DAX) y cuáles no (diseño visual)
- [ ] Repositorio en GitHub con README atractivo (capturas, GIF de demo, badges, licencia)
- [ ] Historial de commits limpio y con convención (`feat:`, `fix:`, `docs:`)
- [ ] Publicado o embebido (Power BI Service/Fabric) y probado en escritorio y móvil
- [ ] Revisión de accesibilidad básica (contraste de color, texto alternativo en imágenes)
- [ ] Post de portafolio redactado (LinkedIn/GitHub Pages) listo para compartir

---

**Siguiente paso sugerido:** elige el dataset (F1 o Sostenibilidad si es tu primer proyecto de este tipo), crea el repo con la estructura de la sección 2, y arranca la Fase 1. Si quieres, en el siguiente mensaje puedo ayudarte a definir el esquema en estrella específico para el dataset que elijas.
