# Design System Premium — Cars Intelligence 2025
### Dirección visual "Smart Car HMI" — inspirada en Tesla, Ferrari, Lamborghini, Porsche y McLaren

## Resumen ejecutivo

Este sistema traslada al dashboard el lenguaje visual de los HMI automotivos de alta gama: precisión suiza de Porsche, agresividad geométrica de Lamborghini, foco funcional de McLaren, contraste dramático de Ferrari y minimalismo tecnológico de Tesla. La dirección elegida es **"cockpit oscuro de precisión"**: fondo casi negro, un único acento cromático de marca (el teal ya establecido), geometría hexagonal como firma visual diferenciadora (heredada de Lamborghini, pero aplicada a KPIs en vez de a rejillas de ventilación), y tipografía de peso variable que jerarquiza dato crudo sobre decoración. El objetivo no es "verse como un auto de lujo" literalmente, sino heredar su disciplina: cada pixel comunica estado o dato, nunca decora porque sí.

## 1. Análisis comparativo de las 5 marcas

| Marca | Paleta/Contraste | Tipografía/Jerarquía | Iconografía | Motion | Layout/Densidad | Material |
|---|---|---|---|---|---|---|
| **Tesla** | Monocromo casi total (negro/blanco/gris), un solo acento funcional (azul en selección activa) | Sans-serif geométrica propia, jerarquía por tamaño y peso, casi sin mayúsculas decorativas | Iconos lineales, sin relleno, mínimos | Transiciones deslizantes suaves, sin ornamento | Muy baja densidad, pantalla dominada por un elemento central | Flat puro, cero skeuomorfismo |
| **Porsche** (Taycan/911) | Negro + acentos plateados/blancos, color reservado para modos de conducción | Tipografía fina, ligera, mucho aire negativo | Instrumento circular curvo que honra el tacómetro analógico de 1963 | Transiciones de precisión, agujas/arcos que animan como mecanismo real | Densidad media, todo organizado en torno al eje del conductor | Vidrio curvo, referencia analógica traducida a digital |
| **Ferrari** | Negro + rojo Corsa de alto contraste, amarillo para alertas | Tipografía condensada, agresiva, orientada a lectura rápida en pista | Iconografía de telemetría (G-force, temperatura de neumáticos) | Animaciones rápidas, feedback inmediato tipo motorsport | Densidad alta en modo pista, doble pantalla piloto/copiloto | Fibra de carbono, texturas técnicas |
| **Lamborghini** (Revuelto/Temerario) | Negro + retroiluminación azul/roja, alto contraste geométrico | Tipografía angular, mayúsculas frecuentes | **Hexágonos y formas "Y"** como sistema de iconos — herencia directa del Miura de los 60 | 3D, animaciones teatrales, arranque como "puesta en escena" | Arquitectura de triple pantalla (cluster + centro + pasajero) | Fibra de carbono real + digital, botón de arranque con tapa roja (skeuomorfismo deliberado) |
| **McLaren** | Negro + un único acento: naranja papaya de competición | Tipografía técnica, aeroespacial, muy poco texto en pantalla | Iconografía mínima, prioriza controles físicos sobre táctiles | Motion casi inexistente — la filosofía es "menos distracción, no más espectáculo" | Densidad muy baja, cluster que se mueve con la columna de dirección | Materiales reales expuestos (carbono visible, no simulado) |

**Patrón común a las cinco:** fondo oscuro casi universal, un solo color de acento por marca (nunca dos compitiendo), y cero relleno decorativo — todo elemento visible existe porque comunica un dato o un estado.
**Diferenciador que vamos a tomar:** el hexágono de Lamborghini es el único patrón geométrico entre las cinco marcas que funciona como sistema de iconos completo, no solo como acento — es el más aplicable a un dashboard de datos, porque un hexágono se presta naturalmente a contener un número central (KPI) rodeado de contexto.

## 2. Fundamentos del sistema

**Color** (extiende, no reemplaza, la paleta ya definida en Checkpoint 6):
- Primario: `#72D6C0` (acento de marca — cumple el rol del "un solo acento" que usan las 5 referencias)
- Secundario geométrico: `#4C6FFF` (para el sistema hexagonal, evita competir con el primario)
- Semánticos: éxito `#79D99A`, alerta `#F1C272`, crítico `#F17272` — igual que antes, sin cambios
- Superficie: `#0F1115` fondo, `#171A20`/`#1E232B` paneles — mantiene la disciplina "negro casi total" de las 5 marcas

**Tipografía:** Segoe UI ya cubre bien el eje "geométrica + legible", pero se añade una regla de **peso variable por jerarquía de dato** (inspirado en Porsche): el número del KPI siempre en Semibold/Bold grande, la unidad y el contexto siempre en peso regular y tamaño reducido — nunca ambos al mismo peso, así el ojo va directo al dato.

**Espaciado y radios:** escala de 4px base (4/8/12/16/24/32). *(Los radios 8/12/18px de la propuesta original quedaron superados por el cambio de canvas a Full HD — ver valores vigentes en "Grid de implementación" abajo.)* Se suma el **hexágono como forma de contenedor alternativa** para KPIs destacados (Performance Index, Value Index), reservado solo para esos dos, para que mantenga estatus de "elemento especial" y no se banalice.

**Grid de implementación (Power BI, Full HD 1920×1080):**

El canvas real del proyecto quedó en 1920×1080 (no 1280×720 como en la propuesta inicial del Checkpoint 6), lo que implica un factor de escala de **1.5x** sobre todos los valores de espaciado y tipografía — no solo sobre las posiciones. Estos son los valores vigentes, y los que hay que usar de acá en adelante para cualquier tarjeta o componente nuevo:

| Elemento | Valor |
|---|---|
| Canvas | 1920 × 1080px |
| Zona de header (`panel2`) | 0,0 — 1920 × 96 |
| Título de página | 36,24 — 600 × 48 |
| Navegador de páginas | 1050,18 — 825 × 60 |
| Margen de contenido | 36,132 — 1848 × 912 |
| Gutter entre tarjetas | 21px |
| Radio — tarjeta estándar | 18px |
| Radio — tarjeta hero/hexágono | 27px |

**Tipografía (escalada 1.5x):**

| Rol | Antes (1280×720) | Vigente (1920×1080) |
|---|---|---|
| Título de página | 16–20px | 24–30px |
| Header de tarjeta | 12px | 18px |
| Label/valor secundario | 10px | 15px |

**Páginas del reporte:** `01_MarketOverview`, `02_PerformanceLab`, `03_ValueIntelligence`, `04_VehicleExplorer` comparten header/nav pixel-idéntico (construidas por duplicación de una página maestra, nunca rehechas a mano una por una). Existe además `_QA_DAX_Profiling` — página de depuración interna, oculta de la navegación pública (clic derecho → Ocultar página) y con prefijo `_` para diferenciarla de las páginas de producto en el panel de Power BI Desktop. No hereda el grid de arriba: mantiene su tamaño y layout libres, ya que no forma parte de la experiencia narrativa del dashboard.

**Sombras/elevación:** 3 niveles únicamente — plano (sin sombra, contenido de fondo), elevado (`0 4px 12px rgba(0,0,0,0.4)`, tarjetas estándar), flotante (`0 8px 24px rgba(114,214,192,0.15)` — sombra tintada con el acento, no negra, para las tarjetas hexagonales destacadas).

**Motion:** duraciones cortas (150–250ms) con easing `cubic-bezier(0.4, 0, 0.2, 1)` para casi todo (entra/sale de tarjetas), y una animación "de precisión" tipo Porsche reservada para los gauges: el arco de un score no salta al valor final, se anima como si fuera una aguja mecánica llegando a su posición (300–500ms, easing `ease-out`).

**Modo claro/oscuro y accesibilidad:** el oscuro es el modo primario (coherente con las 5 marcas — ninguna usa modo claro como default en su cockpit). Para el eventual modo claro, invertir superficies pero conservar el acento `#72D6C0` sin modificar. Contraste verificado: `#EEF2F6` sobre `#0F1115` da ~15.8:1 (supera WCAG AAA); `#AEB7C2` (texto secundario) sobre `#171A20` da ~5.2:1 (cumple AA para texto normal, no AAA — evitar usarlo en texto menor a 14px).

## 3. Inventario de componentes (traducidos a tu dashboard real)

- **Gauge de Performance** (equivalente al velocímetro): arco circular que representa `Performance Index`, con animación de aguja como en Porsche. Contenedor hexagonal opcional para la versión "hero" de la página Performance Lab.
- **Barra de Value Index** (equivalente a indicador de batería/combustible): barra horizontal con el punto de equilibrio en 50, coloreada según `Market Position`.
- **Panel de telemetría** (equivalente a instrumentos secundarios): tabla/lista compacta de specs crudas (HP, Torque, Speed) en tipografía monoespaciada, estilo "readout" de Ferrari.
- **Navegación hexagonal**: los 4 accesos a página (Market Overview, Performance Lab, Value Intelligence, Vehicle Explorer) como iconos hexagonales — aplicación directa del sistema Lamborghini, siendo el elemento de firma visual más reconocible del dashboard.
- **Badge de calidad de dato** (equivalente a notificación): pequeño indicador con color semántico cuando `DataQuality_Flag` señala una incidencia — discreto, nunca modal, siguiendo la filosofía McLaren de "no distraer".
- **Tarjeta de estado del vehículo** (Vehicle Explorer): la ficha hero de cada auto, con foto/silueta, nombre, y los 4 scores en mini-hexágonos alrededor — el componente más "espectáculo" del sistema, reservado a una sola página.

## 4. Guía de estilo — reglas de uso

- El hexágono se usa **solo** para: navegación principal, y los dos índices compuestos (Performance/Value). Nunca para KPIs simples (Average Price, Vehicle Count) — si todo es hexágono, deja de ser una firma visual.
- Un acento cromático por vista. La página puede tener rojo para "Overpriced" y verde para "Best Value" simultáneamente porque son estados de una misma variable categórica — pero nunca dos colores de marca compitiendo por atención.
- Motion siempre con propósito: si una animación no comunica cambio de estado o dato, no se justifica — regla McLaren de "peso visual mínimo".

## 5. Recomendaciones finales para el efecto "wow"

1. Reserva la animación de aguja de precisión (Porsche-style) exclusivamente para cuando el usuario cambia de filtro — es el momento donde más se nota y menos se banaliza.
2. Construye el nav hexagonal como el primer componente SVG del Checkpoint 7: es el elemento que más rápido comunica "esto no es un dashboard genérico de Power BI".
3. En Vehicle Explorer, deja que los mini-hexágonos de score "iluminen" (glow tintado con el acento) solo el que está por encima del percentil 75 — un solo highlight bien colocado comunica más que cuatro elementos igualmente destacados.
