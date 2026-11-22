# Auditoría de Performance, Documentación Final y Caso de Portafolio (Checkpoint 10)

Documento técnico final y ficha de portafolio de **Cars Intelligence 2025**, centrado en eficiencia de motor Tabular/Power BI, decisiones de ingeniería analítica y guía de presentación ejecutiva.

---

## 1. Auditoría de Performance

### 1.1 Capa de datos y motor VertiPaq (Power Query + TMDL)

| Optimización implementada | Impacto técnico | Referencia en el modelo |
|---|---|---|
| **Ingesta de fuente única (`stg_Cars_Raw`)** | Elimina lecturas redundantes del CSV: el archivo fuente se lee y normaliza **una sola vez**, alimentando a `FactVehicle`, `DimCompany`, `DimFuel`, `DimEngine` y las 3 tablas `qa_*` | [`expressions.tmdl`](../powerbi/CarsIntelligence.SemanticModel/definition/expressions.tmdl) |
| **Esquema en estrella compactado** | `FactVehicle` (`1,214` vehículos únicos tras deduplicar 4 filas idénticas) conectado vía relaciones `1:*` hacia 4 dimensiones deduplicadas (`DimCompany`, `DimFuel`, `DimEngine`, `DimPriceSegment`) | [`relationships.tmdl`](../powerbi/CarsIntelligence.SemanticModel/definition/relationships.tmdl) |
| **Compresión e independencia de filtros** | `valueFilterBehavior: independent` habilitado en `model.tmdl` y 71 medidas centralizadas en `_Measures` sin columnas calculadas innecesarias en tablas de hechos salvo donde el motor requiere materialización | [`model.tmdl`](../powerbi/CarsIntelligence.SemanticModel/definition/model.tmdl), [`_Measures.tmdl`](../powerbi/CarsIntelligence.SemanticModel/definition/tables/_Measures.tmdl) |
| **Patrón híbrido Medidas vs. Columnas `(Static)`** | Los 8 índices y posiciones que alimentan **Top N** y filtros nativos se materializan como columnas calculadas `(Static)` en refresh (coste O(1) en tiempo de interacción), mientras los KPIs y gráficos dinámicos evalúan medidas `ALLSELECTED` | [`dax-gotchas.md`](dax-gotchas.md) |

### 1.2 Capa visual y presupuesto por página (PBIR Full HD `1920×1080`)

Microsoft recomienda no superar **20 contenedores visuales por página** para mantener tiempos de renderizado y evaluación de consultas bajo control. Todas las páginas del reporte cumplen con holgura ese presupuesto usando **visuales 100% nativos** (cero SVG dinámico en celdas o tarjetas):

| Página PBIR | Visuales totales | Slicers | Tarjetas KPI | Matriz / Tabla / Gráficos | Nav / Texto / Botones | Cumple ($\le 20$) |
|---|---:|---:|---:|---:|---:|---|
| `00_Home` | **12** | 0 | 4 | 0 | 8 (`1 nav`, `3 text`, `4 actionButton`) | ✅ |
| `01_MarketOverview` | **15** | 4 | 4 | 5 (`pivotTable`, `gauge`, `bar`, `scatter`, `tableEx`) | 2 (`1 nav`, `1 header`) | ✅ |
| `02_PerformanceLab` | **15** | 4 | 4 | 5 (`pivotTable`, `gauge`, `bar`, `scatter`, `tableEx`) | 2 (`1 nav`, `1 header`) | ✅ |
| `03_ValueIntelligence` | **15** | 4 | 4 | 5 (`pivotTable`, `gauge`, `bar`, `scatter`, `tableEx`) | 2 (`1 nav`, `1 header`) | ✅ |
| `04_VehicleExplorer` | **15** | 4 | 4 | 5 (`pivotTable`, `gauge`, `bar`, `scatter`, `tableEx`) | 2 (`1 nav`, `1 header`) | ✅ |

**Controles adicionales de latencia visual:**
- **Top N acotado en tablas detalle (`tableEx`)**: evita renderizar las 1,214 filas sin filtro en cada cambio de segmento.
- **Cero superposiciones geométricas**: validado por `verify_report.py` y la suite E2E de colisiones sobre todo el grid `1920×1080`.
- **Cero sobrecarga SVG en Power BI**: los visuales nativos aprovechan aceleración canvas/DOM estándar y formato condicional nativo (`linearGradient2`).

---

## 2. Caso de Estudio para Portafolio

### Resumen ejecutivo
**Cars Intelligence 2025** convierte un dataset heterogéneo de especificaciones automotrices (precios con rangos y monedas mixtas, desplazamientos con errores de columna y duplicados exactos) en una plataforma bicanal de inteligencia de mercado:
1. **Portal Web interactivo** ([`html/index.html`](../html/index.html)) en estética *Obsidian Dark Luxury* con métricas verificadas, showroom de vehículos reales, inspector de arquitectura y acceso directo a las 4 hojas.
2. **Reporte Power BI PBIP** ([`powerbi/CarsIntelligence.pbip`](../powerbi/CarsIntelligence.pbip)) de **5 páginas visibles** (`00_Home` en tema claro `#F8FAFC` estilo web + `01`–`04` en Bento Grid).

### Hallazgos clave del catálogo 2025
- **Universo limpio**: `1,218` registros crudos $\rightarrow$ **`1,214` vehículos únicos** con **0 colisiones de clave natural** tras auditoría de 11 campos y eliminación de 4 duplicados exactos.
- **Cobertura OEM y electrificación**: **32 fabricantes** (incluyendo separación de `McLaren F1` desde `BMW`), con **`15.8%` de modelos electrificados** (`192` vehículos EV/Híbridos/PHEV).
- **Centro de gravedad del mercado**: precio mediano **`$42,795 USD`**, potencia media **`306 HP`**, velocidad media **`217 km/h`** y aceleración media 0–100 km/h de **`7.6 s`**.
- **Econometría hedónica y oportunidades**: mediante regresión log-lineal ($\ln(\text{HP})$ + velocidad máxima $\rightarrow$ `Hedonic Fair Price (USD)`), se identifican **`459` gemas subvaluadas** con brecha hedónica $\le -15\%$.

> **Nota de rigor metodológico:** Al tratarse de una fotografía transversal de especificaciones del catálogo 2025 sin serie temporal histórica por modelo/año, todas las comparaciones de precio y valor expresan **posicionamiento relativo entre segmentos**, no evolución temporal interanual.

---

## 3. Capturas y material visual del portafolio

| Pieza | Vista | Archivo |
|---|---|---|
| Hero Portal Web (Oscuro) | Portada editorial + telemetría y Porsche Panamera | [`docs/assets/html-portal-preview.png`](assets/html-portal-preview.png) |
| Módulos Analíticos BI | Tarjetas `01`–`04` y arquitectura del modelo | [`docs/assets/html-modules-preview.png`](assets/html-modules-preview.png) |
| Showroom de Vehículos Reales | Galería curada con fotos reales y ficha técnica | [`docs/assets/html-gallery-preview.png`](assets/html-gallery-preview.png) |

---

## 4. Guía rápida para presentación o demo

1. **Presentación rápida sin Power BI**: abrir [`html/index.html`](../html/index.html) en cualquier navegador moderno para recorrer el caso de negocio, las métricas globales, las tarjetas de vehículos reales y el blueprint técnico de las 4 páginas.
2. **Demostración en vivo en Power BI Desktop**: abrir [`powerbi/CarsIntelligence.pbip`](../powerbi/CarsIntelligence.pbip) desde `00_Home`, navegar por `01_MarketOverview` → `04_VehicleExplorer` usando los botones nativos o el navegador superior, y aplicar segmentadores combinados de segmento, combustible, marca y alcance.
3. **Respaldo de ingeniería**: mostrar [`scripts/verify_report.py`](../scripts/verify_report.py), [`scripts/validate_model_mcp.py`](../scripts/validate_model_mcp.py) y el workflow [`.github/workflows/pbip-validate.yml`](../.github/workflows/pbip-validate.yml) como evidencia de calidad reproducible.
