# Proyecto: Análisis de Mercado Automotriz — Cars Datasets (2025)
### Stack: GitHub · MCP · SVG · DAX · HTML (sin LLMs avanzados) — Septiembre 2026

El dataset (`Company, Car Name, Engine, CC/Battery Capacity, HorsePower, Total Speed, Performance 0-100 km/h, Price, Fuel Type, Seats`) es una **foto transversal del mercado en 2025**, no una serie temporal por vehículo. Eso condiciona todo el diseño: no hay "tendencia en el tiempo" real, así que el proyecto se orienta a **segmentación, posicionamiento de precio y relación rendimiento/costo**.

## 1. Objetivo y preguntas de negocio

**Objetivo:** construir un sistema de inteligencia de mercado automotriz que responda, sin depender de modelos de lenguaje, a:

1. ¿Cómo se posiciona cada marca en el eje precio–potencia (HP/USD)?
2. ¿Qué vehículos ofrecen mejor "valor por rendimiento" (aceleración 0-100 km/h vs. precio)?
3. ¿Cómo se distribuye el mercado entre combustión y eléctrico (usando `Fuel Type` y `CC/Battery Capacity`)?
4. ¿Existen segmentos naturales (económico, medio, premium, deportivo, EV-premium) según precio, potencia y plazas?
5. ¿Qué combinaciones de especificaciones técnicas (motor, velocidad máxima) explican los precios más altos?

## 2. Arquitectura técnica

```
Kaggle CSV → GitHub (fuente de verdad) → MCP (automatización) → Power BI (PBIP/TMDL + DAX)
                                                                        ↓
                                              SVG (assets generados) → HTML (informe estático)
```

- **GitHub**: repositorio único como fuente de verdad de datos crudos, modelo (PBIP/TMDL) y assets SVG. Todo cambio es un commit trazable.
- **MCP**: en ausencia de un LLM avanzado, se usa como **capa de automatización determinista**, no generativa: un servidor MCP local (XMLA sobre Power BI Desktop) ejecuta consultas DAX programadas para validar el modelo, detectar nulos o outliers, y exponer el esquema a scripts de CI. No se le pide "razonar"; se le pide ejecutar consultas concretas y devolver resultados tabulares.
- **DAX**: motor de cálculo — segmentación, rankings, ratios valor/precio.
- **SVG**: capa visual vectorial, generada por medidas DAX (data URI) para tarjetas, gauges y mapas de burbujas a medida.
- **HTML**: empaqueta el resultado como informe estático publicable en GitHub Pages, independiente de que el lector tenga Power BI.

## 3. Plan de análisis

1. **Ingesta**: script (`scripts/fetch_dataset.py`, Python + Kaggle API) descarga el CSV, calcula un hash y lo versiona en `data/raw/`.
2. **Limpieza**: separar `CC/Battery Capacity` en dos columnas (`Cilindrada_cc`, `Capacidad_Bateria_kWh`) según `Fuel Type`; normalizar `Price` a una única moneda; imputar/etiquetar nulos en `Seats` y `Total Speed`. Resultado en `data/processed/cars_clean.csv`.
3. **Modelado (Power BI, PBIP/TMDL)**: esquema en estrella — `Fact_Cars` (una fila por vehículo) + `Dim_Company`, `Dim_FuelType`, `Dim_Segmento` (columna calculada por rangos de precio).
4. **Validación automatizada vía MCP**: el servidor MCP local ejecuta un set fijo de consultas DAX (conteo de filas, rango de precios, nulos por columna) tras cada refresh, y el resultado se registra en `docs/qa-log.md` — sustituye la "revisión inteligente" por reglas explícitas.
5. **Construcción de medidas DAX** (ver sección 4).
6. **Diseño visual SVG/HTML** (ver sección 4).
7. **Publicación**: export estático a `docs/index.html` (GitHub Pages) + archivo PBIP en el repo para quien quiera abrirlo en Power BI Desktop.

## 4. Visualizaciones y medidas clave

**Medidas DAX**

```dax
Valor por Rendimiento =
DIVIDE([HP Promedio], [Precio Promedio] / 1000)   -- HP por cada 1,000 USD

Segmento de Precio =
SWITCH(
    TRUE(),
    [Precio Promedio] < 25000, "Económico",
    [Precio Promedio] < 60000, "Medio",
    [Precio Promedio] < 120000, "Premium",
    "Lujo/Deportivo"
)

% Vehículos Eléctricos =
DIVIDE(
    CALCULATE(COUNTROWS(Fact_Cars), Dim_FuelType[Fuel Type] = "Electric"),
    COUNTROWS(Fact_Cars)
)

Ranking Aceleración =
RANKX(ALL(Fact_Cars[Car Name]), [Aceleración 0-100 Promedio], , ASC)
```

**Componente SVG 1 — Tarjeta de marca (generada por DAX, data URI):**
```
[Hexágono con fondo del color de marca]
  ├─ Nombre de la marca (foreignObject, tipografía)
  ├─ Barra horizontal: Precio promedio vs. máximo del mercado
  └─ Icono de rayo/pistón según % eléctrico vs. combustión
```

**Componente SVG 2 — Gauge de aceleración (arco proporcional):**
```dax
Gauge Aceleracion SVG =
VAR t = [Aceleración 0-100 Promedio]
VAR pct = 1 - DIVIDE(t - 2, 10 - 2)   -- normalizado entre 2s (rápido) y 10s (lento)
VAR angulo = pct * 180
RETURN
    "data:image/svg+xml;utf8,<svg width='120' height='70'>" &
    "<path d='M10,60 A50,50 0 0,1 110,60' stroke='#2A2E37' stroke-width='10' fill='none'/>" &
    "<path d='M10,60 A50,50 0 0,1 " & (60 + 50*COS(RADIANS(180-angulo))) & "," &
    (60 - 50*SIN(RADIANS(180-angulo))) & "' stroke='#4C6FFF' stroke-width='10' fill='none'/>" &
    "</svg>"
```

**Componente SVG 3 — Mapa de burbujas Precio vs. HP** (posición X/Y calculada en DAX, radio = plazas, color = tipo de combustible), renderizado como un único SVG que concatena un `<circle>` por vehículo filtrado.

**Informe HTML**: página estática que embebe los SVG exportados + una tabla filtrable en JavaScript puro (sin frameworks), para que el análisis sea consultable sin abrir Power BI — ideal como pieza de portafolio.

## 5. Reproducibilidad y colaboración

- **GitHub** garantiza que cualquier persona pueda clonar el repo, ejecutar `scripts/fetch_dataset.py` y regenerar exactamente el mismo modelo (PBIP/TMDL es texto plano, así que los *pull requests* muestran diffs legibles de cada medida DAX modificada).
- **MCP** actúa como "guardia de calidad" automatizado: en cada PR, un flujo de GitHub Actions puede invocar el servidor MCP local (o un stub headless equivalente) para correr las consultas DAX de validación de la sección 3.4 y bloquear el merge si el conteo de filas o los rangos de precio se desvían de lo esperado — reproducibilidad sin depender de criterio humano ni de un LLM.
- La combinación PBIP + SVG + HTML exportado significa que el proyecto es **verificable por cualquiera**, incluso sin licencia de Power BI: el HTML estático es la prueba tangible del resultado.

## 6. Estructura de archivos

```
cars-2025-analysis/
├── data/{raw,processed}/
├── src/Cars.pbip
│   ├── Cars.Report/            # PBIR
│   └── Cars.SemanticModel/     # TMDL: tablas, medidas, relaciones
├── assets/svg/                 # tarjetas, gauges, plantillas de burbujas
├── docs/
│   ├── index.html              # informe estático (GitHub Pages)
│   └── qa-log.md               # resultados de validación vía MCP
├── scripts/fetch_dataset.py
├── .github/workflows/mcp-validate.yml
└── README.md
```

**Nota de honestidad técnica:** dado que el dataset no tiene dimensión temporal por vehículo, cualquier lenguaje de "tendencia de precios 2025" en el informe final debe matizarse como *comparación transversal entre segmentos*, no como evolución histórica — mantener esa precisión es lo que distingue un análisis senior de uno superficial.
