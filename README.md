# Cars Intelligence 2025

Proyecto de inteligencia de mercado y rendimiento automotriz, construido como experiencia analítica inmersiva sobre el dataset [Cars Datasets (2025)](https://www.kaggle.com/datasets/abdulmalik1518/cars-datasets-2025).

**Stack:** Power BI · DAX · SVG · HTML/CSS · MCP · GitHub

## Objetivo

Transformar el dataset crudo en una interfaz de **Automotive Market & Performance Intelligence**: no un catálogo de autos, sino una herramienta para explorar precio, prestaciones, motorización y posicionamiento relativo de cada vehículo frente al mercado.

## Estado actual

🟢 **Checkpoints 1–5 completos** · 🚧 Checkpoint 6 (Design System) en progreso

| Checkpoint | Objetivo | Estado |
|---|---|---|
| 1 | Repositorio, estructura PBIP, staging inicial | ✅ |
| 2 | Limpieza y normalización (Price, HP, Performance, Seats, Fuel, CC/Battery) | ✅ |
| 3 | Modelo dimensional (`DimCompany`, `DimFuel`, `DimEngine` → `FactVehicle`) | ✅ |
| 4 | Auditoría de calidad de datos (`qa_Cars_Audit`, detección de duplicados) | ✅ |
| 5 | Scores de rendimiento y valor (`Performance Index`, `Value Index`, `Market Position`) | ✅ |
| 6 | Design System: tema importado, canvas Full HD, 4 páginas con header/nav consistente, `01_MarketOverview` construida (KPIs, fuel mix, scatter precio/rendimiento, Top 5 Best Value) | 🚧 En progreso |
| 7 | Componentes SVG dinámicos (KPI bars, score rings, nav hexagonal, badges) | ⬜ |
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

Todas las medidas viven centralizadas en una tabla aislada, **`_Measures`** (migradas desde `FactVehicle`/`DimCompany` antes de iniciar el Checkpoint 6), organizadas por `displayFolder`:

- **`_CORE`** — Conteos base (Vehicle Count, Company Count).
- **`_PRICE` / `_PERFORMANCE`** — Estadísticos descriptivos (Average, Median, Min, Max) de precio, potencia, velocidad, aceleración y torque.
- **`_PROFILE`** — Percentiles P25/P75 para entender la dispersión real del mercado.
- **`_DATA_QUALITY`** — Tasa de calidad, vehículos con incidencias, colisiones de clave natural.
- **`_SCORES`** — Índices de rendimiento y valor (Checkpoint 5): `Score HP`, `Score Speed`, `Score Acceleration`, `Score Torque`, `Performance Index`, `Score Price (Inverted)`, `Value Index`, `Market Position`. Percentil robusto (0–100) dentro del contexto de filtro activo (`ALLSELECTED`), con blancos propagados explícitamente en vez de tratados como 0.

**Columnas `(Static)` en `FactVehicle`** — versión paralela de los 8 scores anteriores, como columnas calculadas (contexto de fila nativo, referencian `ALL(FactVehicle)` en vez de `ALLSELECTED`). Se usan específicamente donde Power BI necesita un valor ya resuelto —Top N nativo y Filtro básico con checkboxes—, algo que una medida no puede ofrecer de forma confiable. Las medidas originales se mantienen para KPIs y gráficos que sí deben reaccionar a filtros de Company/Fuel/Engine. El porqué de esta distinción, con la cadena de errores que llevó a adoptarla, está documentado en [`docs/dax-gotchas.md`](docs/dax-gotchas.md).

## Decisiones y hallazgos de calidad de datos

Durante el Checkpoint 4/5 se auditó la clave de identidad de vehículo (`Vehicle_NaturalKey`) y se encontraron 9 colisiones aparentes. La investigación reveló dos causas distintas, resueltas de forma diferenciada:

1. **Clave insuficiente:** la clave original (`Company|Car_Name|Engine_Raw`) no distinguía variantes/trims con distinto precio, potencia o combustible. Se amplió a una huella de los 11 campos crudos del dataset.
2. **Duplicados de carga reales:** tras ampliar la clave, quedaron 4 filas idénticas en todos los campos salvo el índice técnico — duplicados genuinos del CSV original. Se eliminaron.

**Resultado:** de 1.218 filas originales → **1.214 vehículos únicos**, con 0 colisiones de clave natural.

## Documentación técnica

- [`docs/design-system-premium.md`](docs/design-system-premium.md) — dirección visual del dashboard (paleta, tipografía, motion, inventario de componentes), grid de implementación en Full HD y convención de la página `_QA_DAX_Profiling`.
- [`docs/dax-gotchas.md`](docs/dax-gotchas.md) — lecciones de DAX documentadas a partir de errores reales del proyecto (manejo de blancos, límites del Filtro básico sobre medidas, empates de `RANKX`, contexto de fila vs. agregación, y el criterio medida-vs-columna para ranking/Top N).

## Dataset

Fuente: [Cars Datasets (2025) — Kaggle](https://www.kaggle.com/datasets/abdulmalik1518/cars-datasets-2025)
Columnas originales: Company, Car Name, Engine, CC/Battery Capacity, HorsePower, Total Speed, Performance (0-100 km/h), Price, Fuel Type, Seats, Torque.

## Próximos pasos

Ver tabla de checkpoints arriba. Con `01_MarketOverview` construida, sigue completar `02_PerformanceLab`, `03_ValueIntelligence` y `04_VehicleExplorer` sobre el mismo esqueleto, y luego el nav hexagonal en SVG (Checkpoint 7) como primer componente de identidad visual propia.
