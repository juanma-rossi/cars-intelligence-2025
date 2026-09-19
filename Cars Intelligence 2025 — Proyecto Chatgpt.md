# Cars Intelligence 2025  
### Automotive Market & Performance Intelligence

## 1. Objetivo del proyecto

El objetivo es transformar **Cars Datasets (2025)** en una experiencia de Business Intelligence que permita analizar el posicionamiento de automóviles a partir de precio, prestaciones, motorización y segmento.

Hay una corrección importante respecto de la descripción inicial: la copia verificable del dataset muestra las columnas **Company, Car Name, Engine, CC/Battery, HP, Speed, 0-100 km/h, Price, Fuel y Seats**. Algunas copias derivadas añaden **Torque**, pero no conviene asumir que esa columna está en la versión original sin validarla durante la ingesta. Tampoco se debe asumir que existe una columna de año: la estructura publicada no la muestra.

Por lo tanto, el proyecto no estará orientado a una tendencia histórica de precios, sino a **market positioning y performance intelligence**.

### Preguntas de negocio

1. ¿Qué fabricantes ofrecen la mejor relación **precio/prestaciones**?
2. ¿Cómo cambia el precio según potencia, velocidad máxima y aceleración?
3. ¿Qué marcas dominan distintos niveles del mercado?
4. ¿Existe una prima de precio asociada a determinadas tecnologías de combustible?
5. ¿Qué vehículos son realmente "performance leaders" y cuáles están sobrevalorados respecto de sus prestaciones?
6. ¿Qué combinaciones de potencia, plazas, combustible y precio definen diferentes segmentos de mercado?
7. ¿Cuáles son los vehículos más eficientes desde el punto de vista de **Performance per Dollar**?

La tesis visual del proyecto será:

> **From Car Specs to Market Intelligence**

No se busca crear un catálogo de automóviles, sino un **sistema de inteligencia competitiva automotriz**.

---

# 2. Arquitectura técnica

La arquitectura será deliberadamente simple para respetar la limitación de no depender de grandes modelos de IA.

```text
                 ┌─────────────────────┐
                 │       GitHub        │
                 │ version + docs      │
                 └──────────┬──────────┘
                            │
                            ▼
┌──────────────┐     ┌───────────────┐
│ Kaggle CSV   │ ──► │ Power BI      │
│ Cars 2025    │     │ Data Model    │
└──────────────┘     └───────┬───────┘
                             │
                      ┌──────▼──────┐
                      │     DAX     │
                      │ KPIs/logic  │
                      └──────┬──────┘
                             │
             ┌───────────────┼────────────────┐
             ▼               ▼                ▼
         Native BI         SVG             HTML
         visuals        visual system     UI/cards
             │               │                │
             └───────────────┼────────────────┘
                             ▼
                    Immersive Dashboard
                             ▲
                             │
                      MCP + AI Client
                             │
                    Model/query automation
```

### Rol de cada tecnología

**GitHub**  
Es la fuente de control del proyecto: PBIP/TMDL, DAX, HTML, SVG, documentación y configuración.

**MCP**  
No será utilizado como herramienta ETL. MCP es el puente entre un cliente/agente y el semantic model. El Power BI Modeling MCP permite consultar y modificar modelos semánticos, validar DAX y trabajar con Power BI Project/TMDL. Actualmente está en **Public Preview**, por lo que debe tratarse como una capa experimental y no como dependencia crítica del dashboard.

**DAX**  
Contendrá toda la lógica analítica: precio medio, performance index, ratios, segmentación y rankings.

**SVG**  
Se utilizará para crear componentes visuales dinámicos: speedometers, performance bars, fuel icons, badges y comparadores.

**HTML**  
Será la capa de presentación para tarjetas, fichas de vehículos, paneles de insights y navegación personalizada.

---

# 3. Estrategia considerando la limitación de LLM

No intentaría utilizar MCP como un "analista autónomo".

La estrategia será **human-in-the-loop**:

```text
Analyst
   ↓
defines question
   ↓
MCP
   ↓
executes/query-validates
   ↓
Analyst reviews
   ↓
Git commit
```

Esto es especialmente importante porque Microsoft advierte que el resultado de las operaciones depende del modelo de IA utilizado y recomienda precaución ante cambios inesperados. El servidor local además requiere permisos de escritura para operaciones de modelado.

Con un modelo pequeño, los prompts serán muy concretos:

```text
Inspect the semantic model.

Return:
1. Tables
2. Columns
3. Measures
4. Data types
5. Relationships
6. Potential modeling issues

Do not modify the model.
```

Posteriormente:

```text
Validate this DAX measure.

Check:
- syntax
- filter context
- divide by zero
- unnecessary iterations

Do not modify anything.
```

MCP se utiliza así como una **herramienta de productividad y validación**, no como sustituto del razonamiento analítico.

---

# 4. Plan de análisis

## Etapa 1 — Ingesta

Importar el CSV original y conservar una copia sin modificar.

Crear una primera tabla:

```text
Cars
├── Company
├── Car Name
├── Engine
├── CC/Battery
├── HP
├── Speed
├── 0-100 km/h
├── Price
├── Fuel
└── Seats
```

El dataset publicado es pequeño, aproximadamente 1.200 observaciones según análisis independientes de esta misma fuente, lo que resulta ideal para un dashboard interactivo sin introducir problemas de escala artificiales.

## Etapa 2 — Normalización

Uno de los retos principales será convertir campos que pueden contener unidades y texto en valores numéricos.

Ejemplo conceptual:

```text
"680 HP"       → 680
"350 km/h"     → 350
"3.2 sec"      → 3.2
"$250,000"     → 250000
```

Debe existir una columna original y otra limpia siempre que sea útil para auditoría.

## Etapa 3 — Semantic Model

Aunque exista una única tabla principal, recomiendo separar dimensiones cuando resulte útil:

```text
DimCompany
DimFuel
DimEngine
DimSeats
       │
       ▼
     FactCars
```

El modelo debe mantenerse suficientemente simple: el tamaño del dataset no justifica una arquitectura excesivamente compleja.

## Etapa 4 — Métricas DAX

### Average Price

```DAX
Average Price =
AVERAGE ( Cars[Price] )
```

### Average HP

```DAX
Average HP =
AVERAGE ( Cars[HP] )
```

### Performance Score

Una métrica compuesta puede combinar potencia, velocidad y aceleración:

```DAX
Performance Score =
VAR HPScore =
    DIVIDE ( [Average HP], MAX ( Cars[HP] ) )

VAR SpeedScore =
    DIVIDE ( MAX ( Cars[Speed] ), MAX ( Cars[Speed] ) )

VAR AccelerationScore =
    1 -
    DIVIDE (
        AVERAGE ( Cars[0-100 km/h] ),
        MAX ( Cars[0-100 km/h] )
    )

RETURN
    ( HPScore * 0.40 ) +
    ( SpeedScore * 0.30 ) +
    ( AccelerationScore * 0.30 )
```

En la implementación definitiva conviene normalizar mediante percentiles/min-max correctamente para evitar que los outliers dominen el indicador.

### Performance per Dollar

```DAX
Performance per $ =
DIVIDE (
    [Performance Score],
    [Average Price]
)
```

Esta será una de las métricas distintivas del proyecto.

---

# 5. Visualizaciones innovadoras

## A. Automotive Market Map

Un scatter plot:

```text
Performance
   ▲
   │                    ● Supercar
   │             ●
   │
   │       ●                 ●
   │
   │ ●
   └──────────────────────────────► Price
```

X = Price  
Y = Performance Score  
Size = HP  
Shape/Icon = Fuel  
Color = Company

El objetivo es detectar rápidamente:

- performance leaders;
- premium brands;
- value leaders;
- outliers.

---

## B. SVG Performance Card

Cada automóvil seleccionado tendrá una tarjeta personalizada:

```text
┌──────────────────────────────────┐
│          PERFORMANCE             │
│                                  │
│           845 HP                 │
│       ━━━━━━━━━━━━━━━            │
│           350 KM/H               │
│                                  │
│        0 → 100                   │
│          2.9 SEC                 │
│                                  │
│          ★ 94 / 100              │
└──────────────────────────────────┘
```

El SVG se construirá dinámicamente desde DAX.

Conceptualmente:

```DAX
SVG Performance =
"<svg viewBox='0 0 400 120'>" &
"<rect x='20' y='70' width='" &
    [Performance Bar Width] &
"' height='12' rx='6'/>" &
"<text x='20' y='45'>" &
    FORMAT ( [Performance Score], "0" ) &
"</text>" &
"</svg>"
```

La ventaja es que el mismo componente cambia automáticamente con los filtros.

---

# 6. HTML Automotive Intelligence Card

Una segunda capa será una ficha tipo producto digital:

```html
<div class="car-card">

  <div class="brand">
    COMPANY
  </div>

  <div class="model">
    CAR NAME
  </div>

  <div class="price">
    $250,000
  </div>

  <div class="metrics">
    <span>680 HP</span>
    <span>350 KM/H</span>
    <span>2.9 SEC</span>
  </div>

  <div class="tag">
    PERFORMANCE LEADER
  </div>

</div>
```

La intención visual es que el usuario sienta que está navegando una **aplicación de intelligence**, no una hoja de cálculo.

---

# 7. Diseño final del dashboard

Propongo cuatro páginas.

### 01 — MARKET

```text
MARKET OVERVIEW

[ Cars ] [ Brands ] [ Avg Price ] [ Avg HP ]

        Performance vs Price

─────────────────────────────────────

Brand ranking        Fuel mix
```

### 02 — PERFORMANCE

```text
PERFORMANCE LAB

Selected Car

[ SVG Performance Card ]

HP ──────────────
Speed ───────────
0-100 ───────────
Performance ─────

Benchmark vs competitors
```

### 03 — VALUE

La página más importante para negocio:

```text
VALUE INTELLIGENCE

                    High Performance
                          ▲
                          │
          VALUE           │         PREMIUM
          LEADERS         │
                          │
   ───────────────────────┼──────────────► Price
                          │
          BUDGET          │         OVERPRICED
```

### 04 — EXPLORER

Una experiencia HTML para comparar dos o tres vehículos:

```text
                    CAR A       CAR B

PRICE               $120K       $150K
HP                   450         500
TOP SPEED            300         315
0-100                 3.4         3.1
PERFORMANCE           82          87
VALUE                 91          74
```

---

# 8. GitHub y reproducibilidad

Power BI Project (PBIP) es especialmente adecuado porque almacena el reporte y semantic model como archivos de texto legibles, con estructura preparada para VS Code, Git, colaboración y CI/CD.

La estructura recomendada será:

```text
cars-intelligence-2025/
│
├── README.md
├── LICENSE
├── .gitignore
│
├── powerbi/
│   ├── CarsIntelligence.pbip
│   ├── CarsIntelligence.Report/
│   └── CarsIntelligence.SemanticModel/
│
├── dax/
│   ├── measures.dax
│   ├── performance.dax
│   └── ranking.dax
│
├── svg/
│   ├── performance-card.svg
│   ├── speedometer.svg
│   └── fuel-icons.svg
│
├── html/
│   ├── car-card.html
│   ├── comparison.html
│   └── styles.css
│
├── mcp/
│   ├── prompts/
│   └── README.md
│
├── docs/
│   ├── data-dictionary.md
│   ├── architecture.md
│   └── methodology.md
│
└── screenshots/
```

GitHub no solo almacena el proyecto: documentará la evolución.

Ejemplo:

```bash
git add .
git commit -m "feat: add automotive performance model"
git commit -m "feat: add performance score measures"
git commit -m "feat: add dynamic SVG vehicle card"
git commit -m "feat: add HTML comparison interface"
git commit -m "docs: document MCP workflow"

git push origin main
```

---

# 9. Resultado esperado

El entregable final no será simplemente un Power BI `.pbix`.

Será un **sistema reproducible de Automotive Intelligence**:

```text
                 CARS DATASET
                       │
                       ▼
                SEMANTIC MODEL
                       │
                ┌──────┴──────┐
                ▼             ▼
               DAX           MCP
                │             │
                ▼             ▼
             Metrics       Validation
                │
        ┌───────┴────────┐
        ▼                ▼
       SVG              HTML
        │                │
        └────────┬───────┘
                 ▼
         IMMERSIVE BI APP
                 │
                 ▼
              GitHub
```

La fortaleza del proyecto está precisamente en la integración: **DAX determina la inteligencia, SVG construye el lenguaje visual, HTML construye la experiencia y MCP aporta automatización controlada, mientras GitHub garantiza trazabilidad y reproducibilidad**.

La principal limitación es que el dataset no parece contener una dimensión temporal suficientemente rica para realizar forecasting o tendencias históricas de mercado; tampoco conviene inventar variables que no estén presentes. Por eso, este proyecto debe posicionarse como **Competitive & Performance Intelligence**, no como un sistema de forecasting.

Como resultado de portfolio, eso es incluso más defendible: todas las conclusiones pueden trazarse directamente a las características observadas de los vehículos y a un modelo analítico explícitamente documentado.