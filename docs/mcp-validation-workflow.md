# Flujo de Validación MCP y Desarrollo Reproducible (Checkpoint 9)

Este documento describe cómo **Cars Intelligence 2025** combina **PBIP + TMDL/PBIR** (código fuente en texto plano), **Power BI Modeling MCP** (`powerbi-modeling-mcp`) y validación automatizada en **GitHub Actions** para garantizar calidad de datos, consistencia de medidas DAX y cero regresiones en cada cambio.

---

## 1. Arquitectura de desarrollo reproducible (PBIP + TMDL + PBIR)

El proyecto evita archivos binarios opacos `.pbix` en el control de versiones:

- **Modelo semántico (`powerbi/CarsIntelligence.SemanticModel/definition/`)**: tablas, columnas calculadas, particiones M (`stg_Cars_Raw`), parámetros (`pDataFolder`), relaciones (`relationships.tmdl`) y las **71 medidas DAX** centralizadas en `_Measures.tmdl`.
- **Capa visual (`powerbi/CarsIntelligence.Report/definition/`)**: definición modular de páginas y contenedores en JSON PBIR (`1920×1080`), verificables automáticamente sin abrir Power BI Desktop.
- **Ingesta parametrizada (`pDataFolder`)**: al clonar el repositorio, el archivo CSV crudo (`data/raw/Cars Datasets 2025.csv`, excluido de Git) se enlaza cambiando un único parámetro sin reescribir rutas en múltiples queries.

---

## 2. Integración con Power BI Modeling MCP (`powerbi-modeling-mcp`)

Durante sesiones interactivas con Power BI Desktop abierto, el servidor **Power BI Modeling MCP** permite inspeccionar tablas/medidas y ejecutar consultas `EVALUATE` directamente contra el motor Tabular local.

### Consultas DAX de validación recomendadas vía MCP

1. **Integridad del catálogo, colisiones y cobertura eléctrica**:
   ```dax
   EVALUATE
   ROW(
       "Vehicle_Rows", [Vehicle Rows],
       "Vehicle_Count", [Vehicle Count],
       "Natural_Key_Collisions", [Natural Key Collisions],
       "OEM_Companies", [Company Count],
       "Electrified_Share", [Electrified Share %],
       "Underpriced_Gems", [Underpriced Gems Count],
       "Median_Price_USD", [Median Price],
       "Data_Quality_Rate", [Data Quality Rate %]
   )
   ```
   **Resultados esperados sobre el dataset 2025:**
   - `Vehicle_Rows = 1214` y `Vehicle_Count = 1214` (`1,218` filas crudas menos `4` duplicados exactos).
   - `Natural_Key_Collisions = 0`.
   - `OEM_Companies = 32` (incluyendo reatribución de `BMW` → `MCLAREN` en `McLaren F1`).
   - `Electrified_Share ≈ 15.8%` (`192` vehículos electrificados).
   - `Underpriced_Gems = 459` (brecha hedónica $\le -15\%$).

2. **Rango de scores y ausencia de desbordamientos (`0–100`)**:
   ```dax
   EVALUATE
   ROW(
       "Min_Perf_Static", MIN(FactVehicle[Performance Index (Static)]),
       "Max_Perf_Static", MAX(FactVehicle[Performance Index (Static)]),
       "Min_Value_Static", MIN(FactVehicle[Value Index (Static)]),
       "Max_Value_Static", MAX(FactVehicle[Value Index (Static)]),
       "Out_Of_Range_Perf", CALCULATE(COUNTROWS(FactVehicle), FactVehicle[Performance Index (Static)] < 0 || FactVehicle[Performance Index (Static)] > 100),
       "Out_Of_Range_Value", CALCULATE(COUNTROWS(FactVehicle), FactVehicle[Value Index (Static)] < 0 || FactVehicle[Value Index (Static)] > 100)
   )
   ```
   **Criterio de aceptación:** todos los percentiles permanecen acotados en `[0, 100]` (`Out_Of_Range_* = 0`).

3. **Distribución de posiciones de mercado y auditoría QA**:
   ```dax
   EVALUATE
   SUMMARIZECOLUMNS(
       FactVehicle[Market Position (Static)],
       "Vehicles", [Vehicle Count],
       "Avg_Price", [Average Price],
       "Avg_HP", [Average HP]
   )
   ORDER BY [Vehicles] DESC
   ```

---

## 3. Validación headless local y en CI/CD

Para no depender únicamente de una sesión activa de Power BI Desktop ni de inspección manual, el repositorio ejecuta cuatro capas automatizadas de verificación:

| Capa | Comando | Alcance validado |
|---|---|---|
| Esquema PBIR y Tema | `python scripts/verify_report.py` | **55 checks**: UTF-8 sin BOM en 14 `.tmdl` y 95 `.json`, cero SVG, límites `1920×1080`, cero colisiones visuales, `dropShadow`, tema `#F8FAFC` y enlaces de navegación |
| Guardián MCP / TMDL | `python scripts/validate_model_mcp.py` | **11 checks** (admite `--json`): 9 tablas, `valueFilterBehavior: independent`, 4 relaciones `1:*`, fuente única `stg_Cars_Raw`, paréntesis y metadata en las 71 medidas DAX, presupuesto $\le 20$ visuales/página e invariantes del CSV cuando existe localmente |
| Suite E2E multi-nivel | `python tests/run_e2e_tests.py` | **309 pruebas** de funcionalidades, límites geométricos, combinaciones entre páginas `00`–`04`, portal HTML y escenarios de negocio |
| Regresión + Mutaciones | `python -m pytest tests/ -q` | **322 tests**, incluyendo pruebas adversariales de mutación para asegurar que el validador detecta fallos reales |

### Pipeline automatizado en GitHub Actions

El workflow [`.github/workflows/pbip-validate.yml`](../.github/workflows/pbip-validate.yml) corre automáticamente en cada `push` y `pull_request` hacia `main` sobre `ubuntu-latest` con Python `3.12`, ejecutando los cuatro scripts anteriores en secuencia (`validate_model_mcp.py` omite limpiamente `[SKIP]` la comprobación del CSV crudo ya que `data/raw/*.csv` está excluido en `.gitignore`).

---

## 4. Log de validación QA verificado

| Fecha | Entorno | Verificación ejecutada | Resultado |
|---|---|---|---|
| 2026-11-22 | Local Windows (Python 3.12) | `python scripts/verify_report.py` | **55 PASSED \| 0 FAILED \| 0 WARNINGS** |
| 2026-11-22 | Local Windows (Python 3.12) | `python scripts/validate_model_mcp.py` | **11 PASSED \| 0 FAILED \| 0 SKIPPED** |
| 2026-11-22 | Local Windows (Python 3.12) | `python tests/run_e2e_tests.py` | **309 / 309 PASSED** |
| 2026-11-22 | Local Windows (Python 3.12) | `python -m pytest tests/ -q` | **322 passed** |
