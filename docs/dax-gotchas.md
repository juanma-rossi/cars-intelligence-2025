# DAX Gotchas — Cars Intelligence 2025

Lecciones extraídas de construir el ranking "Top 5 Best Value" en `01_MarketOverview`. Costó varias iteraciones porque cada síntoma parecía un bug nuevo, cuando en realidad todos venían de una sola causa raíz (ver lección 6). Se documenta acá para no volver a perder tiempo la próxima vez que se necesite un ranking o un Top N en este modelo.

## 1. `BLANK()` se compara como `0`, no como "ausente"

**Síntoma:** un filtro `<= 5` sobre una medida que debía devolver blanco para "no aplica" dejaba pasar casi todas las filas.
**Causa:** en una comparación numérica, DAX trata `BLANK()` como `0`. `BLANK() <= 5` se evalúa como `0 <= 5` → verdadero.
**Regla:** si una medida puede devolver blanco y se va a usar en un filtro numérico, hay que neutralizar el blanco explícitamente — con un valor centinela imposible de confundir (ej. `9999`), o verificando `NOT ISBLANK(...)` como condición aparte, nunca confiando en que "blanco" se comporte como "no cuenta".

## 2. Las medidas no ofrecen Filtro básico (checkboxes) en el panel de Filtros

**Síntoma:** al arrastrar una medida de texto o booleana al pozo de filtros de un visual, no aparece la lista de valores para tildar — solo queda disponible el Filtro avanzado.
**Causa:** el Filtro básico necesita una lista de valores distintos precalculada, algo que solo existe para columnas (valores fijos almacenados). Una medida se evalúa en el momento, según el contexto, así que no hay lista fija que mostrar — aplica igual a medidas de texto (`Market Position`) y a medidas booleanas (`Es Top 5 Best Value`).
**Regla:** si un campo se va a usar para filtrar con checkboxes, tiene que ser una columna. Para lógica que solo existe como medida, usar Filtro avanzado — y si el avanzado se comporta de forma inconsistente, considerar materializar el resultado como columna calculada (ver lección 6).

## 3. `RANKX` no desempata solo — genera huecos (ranking de competencia)

**Síntoma:** al rankear por `Value Index`, la tabla "Top 5" arrancaba en el puesto 25 en vez de 1.
**Causa:** `RANKX` usa por defecto ranking de competencia: si 24 filas empatan en el valor más alto, las 24 reciben rank 1, y la siguiente fila distinta salta directo al rank 25. No faltaba nada — los primeros 24 puestos estaban todos apilados en el valor 1.
**Regla:** antes de asumir que un ranking "saltó" valores por error, ordenar la columna de rank ascendente y mirar cuántas filas comparten el rank más bajo. Si hay empates reales, hace falta un criterio de desempate explícito y documentado (ver lección 6 para por qué el desempate dentro de una medida es frágil).

## 4. Una columna envuelta en `MAX()` sin `CALCULATE`, dentro de un iterador, no respeta el contexto de fila

**Síntoma:** un término de desempate con `MAX(FactVehicle[Price_Avg_USD])` dentro de la expresión de `RANKX` devolvía el mismo valor para todas las filas (el máximo de todo el grupo filtrado, no el de cada vehículo).
**Causa:** una función de agregación simple como `MAX()` evaluada dentro de un contexto de fila no hace automáticamente la transición de contexto de fila a contexto de filtro — sigue mirando el contexto de filtro ambiente completo.
**Regla:** para forzar que una agregación se acote a la fila que se está iterando en ese momento, envolverla en `CALCULATE()`: `CALCULATE(MAX(FactVehicle[Columna]))`. Sin el `CALCULATE`, el resultado es silenciosamente incorrecto — no tira error, solo da el mismo número para todas las filas.

## 5. El prefijo `@` en `ADDCOLUMNS` solo es válido dentro del mismo `ADDCOLUMNS`

**Síntoma:** error *"The value for '@Score' cannot be determined"*.
**Causa:** `@NombreColumna` sirve únicamente para referenciar, dentro de la misma llamada a `ADDCOLUMNS`, una columna agregada en un paso anterior de esa llamada (evita ambigüedad cuando una columna nueva depende de otra). Una vez que la tabla ya está construida y se referencia desde afuera (ej. dentro de `RANKX`), la columna se nombra sin `@`, como cualquier columna normal.
**Regla:** `@` es sintaxis interna de `ADDCOLUMNS`, no una forma general de apuntar a una columna calculada.

## 6. La lección de fondo: medida vs. columna calculada no son intercambiables para ranking/Top N

Todos los síntomas anteriores vinieron de forzar una **medida** (`Market Position`, `Value Index`) a comportarse como una **columna** dentro de filtros y rankings de un visual. Una medida se recalcula según el contexto activo — por diseño, no tiene "un valor fijo" hasta que algo la evalúa. Eso la hace ideal para tarjetas y gráficos que deben reaccionar a filtros de Company/Fuel, pero la vuelve frágil para Top N y Filtro básico, que esperan valores ya resueltos.

**Patrón que funcionó:** crear una versión `(Static)` de cada score como **columna calculada** (contexto de fila nativo, sin `SELECTEDVALUE` ni transición de contexto que gestionar, referenciando `ALL(FactVehicle)` en vez de `ALLSELECTED`):

```dax
Score HP (Static) =
VAR _hp = FactVehicle[HorsePower_Avg]
VAR _total = COUNTROWS(FILTER(ALL(FactVehicle), NOT ISBLANK(FactVehicle[HorsePower_Avg])))
VAR _menorOIgual = COUNTROWS(FILTER(ALL(FactVehicle), FactVehicle[HorsePower_Avg] <= _hp && NOT ISBLANK(FactVehicle[HorsePower_Avg])))
RETURN IF(ISBLANK(_hp), BLANK(), DIVIDE(_menorOIgual, _total) * 100)
```

**Cuándo usar cada una:**

| Necesidad | Usar |
|---|---|
| KPI/tarjeta que debe reaccionar a filtros de Company, Fuel, Engine | Medida (`Score HP`, `Performance Index`, `Market Position`) |
| Scatter/gráfico donde el eje debe recalcularse según el filtro activo | Medida |
| Top N nativo de un visual | Columna `(Static)` |
| Filtro básico (checkboxes) sobre una categoría derivada | Columna `(Static)` |
| Cualquier ranking con posible empate | Columna `(Static)` — el Top N nativo de Power BI maneja empates correctamente (incluye todos los empatados en el límite) sin necesidad de `RANKX` manual |

Las medidas originales **no se eliminaron** — siguen siendo la opción correcta donde la reactividad a filtros es el requisito. Las columnas `(Static)` conviven con ellas, para un propósito distinto.
