# Cars Intelligence 2025

Proyecto de inteligencia de mercado y rendimiento automotriz, construido como experiencia analítica inmersiva sobre el dataset [Cars Datasets (2025)](https://www.kaggle.com/datasets/abdulmalik1518/cars-datasets-2025).

**Stack:** Power BI · DAX · SVG · HTML/CSS · MCP · GitHub

## Objetivo

Transformar el dataset crudo en una interfaz de **Automotive Market & Performance Intelligence**: no un catálogo de autos, sino una herramienta para explorar precio, prestaciones, motorización y posicionamiento relativo de cada vehículo frente al mercado.

## Estado actual

🟢 **Checkpoints 1–5 completos** · 🚧 Checkpoint 6 (Design System) en preparación

| Checkpoint | Objetivo | Estado |
|---|---|---|
| 1 | Repositorio, estructura PBIP, staging inicial | ✅ |
| 2 | Limpieza y normalización (Price, HP, Performance, Seats, Fuel, CC/Battery) | ✅ |
| 3 | Modelo dimensional (`DimCompany`, `DimFuel`, `DimEngine` → `FactVehicle`) | ✅ |
| 4 | Auditoría de calidad de datos (`qa_Cars_Audit`, detección de duplicados) | ✅ |
| 5 | Scores de rendimiento y valor (`Performance Index`, `Value Index`, `Market Position`) | ✅ |
| 6 | Design System: paleta, tipografía, grid, navegación | 🚧 Próximo |
| 7 | Componentes SVG dinámicos (KPI bars, score rings, badges) | ⬜ |
| 8 | HTML/CSS: fichas de vehículo, comparación, narrativa | ⬜ |
| 9 | MCP: validación de modelo y flujo de desarrollo reproducible | ⬜ |
| 10 | Performance, documentación final, screenshots, portafolio | ⬜ |

## Arquitectura de datos

**Ingesta consolidada en una sola fuente de verdad.** Todas las tablas del modelo (`FactVehicle`, `DimCompany`, `DimFuel`, `DimEngine`, tablas `qa_*`) referencian una única query de staging, `stg_Cars_Raw`, en vez de reprocesar el CSV crudo de forma independiente. Esto se corrigió durante el desarrollo (ver *Decisiones y hallazgos de calidad* abajo) para que el proyecto sea reproducible al clonarlo.

```
stg_Cars_Raw (única lectura + limpieza del CSV, vía parámetro pDataFolder)
      │
      ├── FactVehicle   (hechos: un registro por vehículo)
      ├── DimCompany    (marca, deduplicada)
      ├── DimFuel       (grupo de combustible, deduplicado)
      ├── DimEngine     (motor normalizado, deduplicado)
      └── qa_*          (auditoría de calidad y duplicados)
```

**Modelo semántico:** esquema en estrella, relaciones 1:* de `FactVehicle` hacia cada dimensión, formato **PBIP + TMDL** (texto plano) para que los cambios se puedan revisar como diffs legibles en cada Pull Request.

### Reproducir el proyecto localmente

1. Clona el repositorio y coloca el CSV en `data/raw/Cars Datasets 2025.csv`.
2. Abre `CarsIntelligence.pbip` en Power BI Desktop.
3. En **Transformar datos → Administrar parámetros**, actualiza `pDataFolder` con la ruta local a tu carpeta `data/raw`.
4. Actualiza el modelo (Inicio → Actualizar).

## Modelo DAX

Medidas organizadas por `displayFolder` dentro de `FactVehicle`:

- **`_CORE`** — Conteos base (Vehicle Count, Company Count).
- **`_PRICE` / `_PERFORMANCE`** — Estadísticos descriptivos (Average, Median, Min, Max) de precio, potencia, velocidad, aceleración y torque.
- **`_PROFILE`** — Percentiles P25/P75 para entender la dispersión real del mercado.
- **`_DATA_QUALITY`** — Tasa de calidad, vehículos con incidencias, colisiones de clave natural.
- **`_SCORES`** — Índices de rendimiento y valor (Checkpoint 5): `Score HP`, `Score Speed`, `Score Acceleration`, `Score Torque`, `Performance Index`, `Score Price (Inverted)`, `Value Index`, `Market Position`. Calculados como percentil robusto (0–100) dentro del contexto de filtro activo (`ALLSELECTED`), evitando pesos arbitrarios y baja sensibilidad a outliers.

> Nota de diseño: por ahora las medidas viven dentro de `FactVehicle`. Migrarlas a una tabla `_Measures` aislada queda como tarea de limpieza pendiente antes del Checkpoint 6.

## Decisiones y hallazgos de calidad de datos

Durante el Checkpoint 4/5 se auditó la clave de identidad de vehículo (`Vehicle_NaturalKey`) y se encontraron 9 colisiones aparentes. La investigación reveló dos causas distintas, resueltas de forma diferenciada:

1. **Clave insuficiente:** la clave original (`Company|Car_Name|Engine_Raw`) no distinguía variantes/trims con distinto precio, potencia o combustible. Se amplió a una huella de los 11 campos crudos del dataset.
2. **Duplicados de carga reales:** tras ampliar la clave, quedaron 4 filas idénticas en todos los campos salvo el índice técnico — duplicados genuinos del CSV original. Se eliminaron.

**Resultado:** de 1.218 filas originales → **1.214 vehículos únicos**, con 0 colisiones de clave natural.

## Dataset

Fuente: [Cars Datasets (2025) — Kaggle](https://www.kaggle.com/datasets/abdulmalik1518/cars-datasets-2025)
Columnas originales: Company, Car Name, Engine, CC/Battery Capacity, HorsePower, Total Speed, Performance (0-100 km/h), Price, Fuel Type, Seats, Torque.

## Próximos pasos

Ver tabla de checkpoints arriba. El siguiente hito es el Design System (Checkpoint 6): paleta de color, tipografía y grid que servirán de base para los componentes SVG/HTML de los checkpoints 7 y 8.