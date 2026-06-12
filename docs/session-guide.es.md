# Guion de sesión — Build Interactive Agents with Generative UI on Azure

Guion para una sesión técnica de 45–60 minutos que recorre el espectro de Generative UI (Controlled → Declarative → Open-Ended) con las tres demos de este repositorio. La referencia conceptual en inglés está en [generative-ui-spectrum.md](generative-ui-spectrum.md).

## Preparación (antes de la sesión)

1. Arranca **los tres pares de procesos** (pueden convivir; cambiar de demo no requiere reiniciar nada):

   ```bash
   npm run dev:controlled-agent    # :8123 — requiere Foundry + Databricks (o apunta al Hosted Agent)
   npm run dev:controlled-web      # :3000
   npm run dev:declarative-agent   # :8124 — solo necesita RISK_MODEL_ENDPOINT
   npm run dev:declarative-web     # :3001
   npm run dev:open-ended-agent    # :8125 — solo necesita RISK_MODEL_ENDPOINT
   npm run dev:open-ended-web      # :3002
   ```

2. Verifica los tres health checks: `curl localhost:8123/health localhost:8124/health localhost:8125/health`.
3. Ten las tres pestañas abiertas (3000 / 3001 / 3002) y el SQL Warehouse de Databricks arrancado (la primera consulta Genie tarda si está frío).
4. Ensaya el beat 3 (open-ended) una vez antes de la sesión: el modelo inventa el layout y conviene saber qué esperar ese día.

## Estructura propuesta (50 min)

| Bloque | Tiempo | Contenido |
| --- | --- | --- |
| 1. Conceptos | 8 min | El espectro de Generative UI y AG-UI como transporte |
| 2. Demo Controlled | 15 min | Genie + dashboard + frontend tools |
| 3. Demo Declarative | 10 min | A2UI: catálogo custom, fixed + dynamic schema |
| 4. Demo Open-Ended | 8 min | Sandboxed UI (`openGenerativeUI`) + MCP Apps (Excalidraw) |
| 5. Gobernanza y producción | 6 min | Cuándo usar cada banda; camino a producción |
| 6. Q&A | 5 min | — |

## Bloque 1 — Conceptos (8 min)

Ideas que conviene fijar antes de tocar las demos:

- **Generative UI** = el agente participa en decidir la interfaz, no solo el texto. No es binario: es un espectro de cuánta autoría cede el desarrollador.
- **Las tres bandas**: Controlled (el desarrollador entrega componentes; el agente elige cuál y con qué datos), Declarative (el agente compone layouts desde un catálogo de bloques — A2UI), Open-Ended (el agente inventa la interfaz).
- **AG-UI es el transporte** (eventos: mensajes, tool calls, estado, eventos custom) y **A2UI es un payload** que viaja sobre él (operaciones `createSurface` / `updateComponents` / `updateDataModel`).
- Anuncia la tesis de la sesión: *misma arquitectura (LangGraph + AG-UI + CopilotKit + Foundry), tres niveles de autoría*.

## Bloque 2 — Demo Controlled (15 min) · `localhost:3000`

1. **Prompt**: `What is the total exposure by country in 2026-Q2?`
   - Señala el **status timeline** (eventos custom AG-UI `risk_ui_event`): supervisión → plan → consulta gobernada → normalización → visualización → procedencia.
   - Señala los **chips de tool-calls** en el chat y cómo el dashboard se construye con componentes React propios (Recharts) validados con Zod.
   - Mensaje clave: el agente emite tool-calls *pre-resueltos*; el frontend valida cada payload antes de mutar nada. Determinismo total.
2. **Prompt**: `Add a donut chart of claims by broker` (u operación similar sobre datos ya cacheados)
   - Mensaje clave: el `dashboard_op` deriva visuales de datasets cacheados sin volver a consultar Genie.
3. **Frontend tools (wow)** — el agente maneja la aplicación, no solo el chat:
   - `Spotlight the bar chart` → la card escala a ancho completo y el resto se atenúa.
   - `Enter presentation mode` → desaparece el chrome de la app (hero y pills) y se ensancha el lienzo.
   - `Exit presentation mode and clear the spotlight` → restaurado.
   - ⚠️ Estos comandos requieren que el dashboard ya exista (el guard de `dashboard_op` pide datos cacheados): hazlos siempre después del paso 1.
4. Si hay tiempo: enseña en el portal de Foundry las sesiones/trazas del hosted agent (dos agentes: orquestador AG-UI + prompt agent con tool MCP de Genie).

## Bloque 3 — Demo Declarative (10 min) · `localhost:3001`

La analogía Lego del curso: el **catálogo** es la caja de piezas, el **schema** dice cómo encajan, los **data bindings** rellenan los datos. Enseña 20 segundos de `apps/declarative/web/src/catalog/definitions.ts` ("estas son las piezas que YO defino") antes de los prompts.

1. **Fixed schema** — `Give me the executive risk report for 2026-Q2`
   - Superficie A2UI en el chat: fila de KPI cards con tendencias ↑↓, bar chart real de exposure por país, ranking, tabla de detalle; el agente cierra con un resumen de dos frases (lo único que escribe el LLM).
   - Mensaje clave: el layout está **pre-autorado** (`report_catalog.py`) y se puede revisar en PR — los tests de contrato validan árbol y bindings en CI. El frontend no registra ningún componente con el agente: solo define el catálogo.
2. **Fixed, recompuesto** — `Show the compact risk brief for 2026-Q1 instead`
   - Mismas piezas, otro layout (pie chart, KPIs en fila). El LLM solo eligió `brief` + trimestre.
3. **Dynamic schema** — `Compose a risk dashboard your way — pick the catalog components you think fit best`
   - Aquí está el momento wow: el LLM **compone el layout él mismo** con las mismas piezas, y la superficie se construye **progresivamente** en el chat (el middleware parsea los args de `render_a2ui` en streaming — verás Title → Metrics → BarChart → PieChart → DataTable apareciendo por orden).
   - Mensaje clave: fixed y dynamic son la MISMA banda — cambia quién compone, no el vocabulario. Tabla del curso: fixed para superficies pulidas de alto tráfico; dynamic para el long tail.
4. Menciona el [A2UI Composer](https://a2ui-editor.ag-ui.com/) (editor visual con el que se autorizan los fixed schemas — 30 segundos en pantalla quedan muy bien).

## Bloque 4 — Demo Open-Ended (8 min) · `localhost:3002`

Sin componentes registrados y sin catálogo: el extremo abierto del espectro (L5 del curso).

1. **Sandboxed UI** — `Build me an animated live-status widget for this energy risk portfolio — get creative`
   - El agente escribe HTML/CSS/JS de cero (tool `generateSandboxedUi`, activado con una línea: `openGenerativeUI: true`) y la UI **se va pintando mientras el modelo la escribe** dentro de un iframe sandboxed.
   - Señala el orden de streaming (css → html → js) y el sandbox (sin same-origin; CDNs permitidos).
2. **MCP App** — `Draw the architecture of this demo (browser, CopilotKit runtime, AG-UI agent, Foundry model) on an Excalidraw whiteboard`
   - El runtime descubre los tools del servidor MCP de Excalidraw y embebe la **app completa** en el chat; el agente dibuja el diagrama. Mismo protocolo de apps que usan Claude y ChatGPT.
   - ⚠️ Requiere internet hacia `mcp.excalidraw.com`.
3. **Repite el prompt del widget**: sale otra UI distinta. *Esa variación es la demo* — y el caveat de gobernanza: sin pre-revisión posible, los contratos de los tools son la única valla.

## Bloque 5 — Gobernanza y producción (6 min)

- Matriz de decisión: analítica gobernada y cara a ejecutivos → Controlled; informes componibles con vocabulario acotado → Declarative; exploración/prototipado y superficies efímeras → Open-Ended.
- El 80 % de la calidad en producción está en la capa semántica (vistas Unity Catalog, consultas confiables), no en el tuning del agente — ver [scaling-to-production.md](scaling-to-production.md).
- Pins de versión (`1.55.2-next.1` / `copilotkit>=0.1.89`) como práctica para demos reproducibles.

## Guion de prompts por demo

Secuencias listas para copiar/pegar, con munición extra si la audiencia pide más. En español funcionan igual (los agentes responden en tu idioma).

### Demo 1 · Controlled (`localhost:3000`)

| # | Prompt | Qué demuestra |
| --- | --- | --- |
| 1 | `What is the total exposure by country in 2026-Q2?` | Ruta `risk_data`: timeline + Genie + dashboard con tool-calls validados |
| 2 | *(clic en un follow-up propuesto)* | `followUpQuestions` re-invoca al agente |
| 3 | `Add a donut chart of exposure by country` | `dashboard_op` deriva del dataset cacheado, sin volver a Genie |
| 4 | `Change the donut to a line chart` | Re-tipado in place, mismos datos |
| 5 | `Show me the brokers with the highest total claim amount` | Segundo dataset cacheado conviviendo |
| 6 | `Spotlight the bar chart` | Frontend tool: resuelve "the bar chart" → id y maneja la vista |
| 7 | `Enter presentation mode` | El agente controla el shell de la app |
| 8 | `Exit presentation mode and clear the spotlight` | Restauración por el mismo carril controlado |

Extras: `What can you do?` (ruta `direct` — el agente decide que NO hace falta UI) · `Remove the chart` con varios charts (devuelve `none` y pide aclaración).

### Demo 2 · Declarative (`localhost:3001`)

| # | Prompt | Qué demuestra |
| --- | --- | --- |
| 1 | `Give me the executive risk report for 2026-Q2` | Fixed: layout pre-autorado (KPIs con tendencia, bar chart, ranking, tabla) |
| 2 | `Show the compact risk brief for 2026-Q1 instead` | Fixed recompuesto: mismas piezas, otro layout |
| 3 | `Compose a risk dashboard your way — pick the catalog components you think fit best` | Dynamic: el LLM compone y se renderiza progresivamente |

Extras (dynamic): `Now compose a view comparing 2026-Q1 vs 2026-Q2 — whatever components tell that story best` · `Focus it on Spain only, with a badge flagging anything concerning` · `Why did you pick those components?` (momento meta).

### Demo 3 · Open-Ended (`localhost:3002`)

| # | Prompt | Qué demuestra |
| --- | --- | --- |
| 1 | `Build me an animated live-status widget for this energy risk portfolio — get creative` | `generateSandboxedUi`: HTML/CSS/JS pintándose en streaming |
| 2 | `Draw the architecture of this demo (browser, CopilotKit runtime, AG-UI agent, Foundry model) on an Excalidraw whiteboard` | MCP App embebida; el middleware ejecuta el tool contra el servidor |
| 3 | *(repite el prompt 1 tal cual)* | No-determinismo: misma petición, otra interfaz |

Extras: `Add labels and arrows and make the diagram more coherent` (iteración sobre la pizarra) · `Build an interactive what-if calculator: a slider for exposure growth % that updates the projected totals live` (JS interactivo en el sandbox) · `Make it rain little wind turbines and solar panels over a card that says Acciona Energía` (cierre con risa).

## Fallbacks si algo falla en directo

| Problema | Plan B |
| --- | --- |
| Genie/Databricks no responde (warehouse frío, red del evento) | Salta a la demo 2: no depende de Databricks y mantiene la narrativa A2UI. Mientras, relanza el warehouse. |
| El modo dynamic (demo 2) genera un layout raro o inválido | Re-prompt ensayado: `That layout failed — compose it again, simpler: a Column with three Metrics and one BarChart.` Si reincide, los beats fixed cuentan la misma historia con determinismo total. |
| Spotlight/presentation mode no hacen nada | Casi seguro no hay dashboard todavía — lanza primero la consulta de exposure del bloque 2. |
| El supervisor enruta mal una petición | Reformula con las suggestion chips de cada app (están curadas por banda y por modo). |
| Excalidraw no carga (sin internet hacia mcp.excalidraw.com) | Quédate con el beat de sandboxed UI (solo necesita el modelo) y enseña MCP Apps con una captura; el concepto queda igual de claro. |
| Turbopack se queda en "compiling" eterno (panic esporádico de `next dev`) | Mata y relanza ese `dev:*-web`; la página recompila en segundos. |
| Sin red estable para Foundry | Los beats FIXED de la demo 2 funcionan **sin ningún modelo**: una heurística por palabras clave elige layout y trimestre, el informe A2UI renderiza igual (layout y datos son deterministas) y solo el resumen pasa a ser "canned". Dynamic y demo 3 sí necesitan modelo. |

## Cierre

```bash
source .risk.env.local && ./scripts/stop-compute.sh   # apaga el SQL Warehouse tras la sesión
```

Deja como referencia para la audiencia: [generative-ui-spectrum.md](generative-ui-spectrum.md) (mapa banda → demo → ficheros) y el curso de DeepLearning.AI.
