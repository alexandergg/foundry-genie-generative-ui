# Escalado a producción: Genie, Foundry y context engineering

Notas estratégicas sobre cómo evolucionar esta solución (Foundry hosted agent + Genie MCP + AG-UI + Controlled Generative UI) hacia escenarios de producción con tablas complejas, relaciones, muchas columnas y miles de registros en Databricks.

## TL;DR

La arquitectura sí escala (Foundry hosted agent + Genie MCP + AG-UI + Controlled Generative UI). Lo que no escala automáticamente es la calidad de respuestas cuando el modelo de datos crece: eso depende casi al 100% de cómo prepares el semantic layer en Unity Catalog y los trusted assets del Genie Space. El agente de Foundry está bien planteado, pero hoy es "monolítico" y con memoria corta — para producción te interesa router + sub-agentes por dominio + memoria de largo plazo.

---

## 1. Escalabilidad de lo que tienes hoy

Lo que escala bien tal cual:

- Foundry hosted agent (`risk-exposure-ag-ui-hosted`) y la separación con el prompt agent (`risk-exposure-genie-agent`) — buen patrón, te permite poner N prompt agents detrás del mismo runtime.
- Genie MCP como tool — Genie ya hace el SQL planning, retries, follow-up disambiguation. Tu agente no tiene que aprender a hacer SQL.
- Controlled Generative UI — clave: aunque las tablas crezcan, tú sigues renderizando con un set fijo de componentes. La complejidad de datos no degrada la UI.
- Conversation memory de Foundry (`azure_ai_agents_conversation_id`) — ya está bien usada para no re-llamar a Genie cuando la respuesta vive en el hilo.

Lo que no escala con el modelo actual:

- Un único Genie Space: a partir de ~30-50 tablas o varios dominios (riesgo + claims + finance + comercial), un solo Space se vuelve lento y ambiguo.
- Schema/contexto implícito: hoy confías en `vw_risk_genie_exposure_claims`. Sin esa vista, Genie tendría que razonar sobre joins por su cuenta — eso es donde Genie falla en producción.
- System prompt estático: `_genie_business_prompt` no se adapta al rol del usuario, ni a qué dominio pregunta, ni a métricas/KPIs propios de su negocio.
- Sin memoria larga: cada sesión empieza de cero. No hay "el usuario X siempre filtra por EMEA" o "esta empresa llama 'exposure' a otra cosa".

---

## 2. Databricks/Genie — qué hacer para producción

El 80% de la calidad en escenarios complejos se gana aquí, no en el agente.

### Semantic layer en Unity Catalog (lo más importante)

- Crea vistas curadas por dominio (como `vw_risk_genie_exposure_claims`) que ya resuelvan los joins ambiguos, expongan nombres "de negocio" y oculten columnas internas. Genie va a ser dramáticamente más fiable contra 5 vistas bien diseñadas que contra 80 tablas crudas.
- Pon column comments ricos (lo que ya haces en `risk_demo_setup.sql` — escálalo). Genie lo lee como contexto.
- Usa Unity Catalog Metric Views (GA en 2025) para definir KPIs reutilizables (`overdue_rate`, `gross_exposure_eur`) una sola vez, con sus dimensiones permitidas.
- Aplica row-level security y column masks vía UC (`ROW FILTER` + `MASK`). Con OBO (on-behalf-of) en el MCP, Genie respeta el RBAC del usuario que pregunta.

### Configuración del Genie Space

- Instructions (general + SQL): define glosario ("exposure" = `exposure_eur - overdue_balance_eur`, "active broker" = broker con póliza en últimos 4Q, etc.).
- Certified/trusted queries: añade 15-30 SQL ejemplo certificados por un analista. Esto es lo que más sube el acierto en preguntas complejas. Genie los usa como few-shot.
- Sample values per column para columnas de cardinalidad media (segmento, país, risk_class) — desambigua "muéstrame DACH" → `country IN ('Germany','Austria','Switzerland')`.
- Excluded columns: oculta PII / técnicas (`_etl_ts`, hashes) — reduce ruido y superficie de leak.

### Múltiples Genie Spaces por dominio (cuando el modelo crezca)

- Un Space por dominio (Risk, Claims, Finance, Commercial). Cada uno con sus vistas y trusted queries.
- En el agente, conviertes el "tool único Genie" en N tools (`query_risk`, `query_claims`, `query_finance`) y dejas que el modelo elija. Hoy en `foundry_agent_client.py` ya tienes un router de rutas (`direct/dashboard_op/risk_data`); lo extiendes para que `risk_data` se sub-rute a un dominio concreto.

### Rendimiento

- SQL Warehouse Serverless (escalado automático en segundos) en vez de classic — crítico cuando hay concurrencia.
- Z-ORDER y partitioning en las facts grandes (por `fiscal_quarter`, `country`).
- Materialized views para los agregados que el dashboard pide siempre (top-N por país, trends por quarter). Genie las usará si la métrica encaja.
- Photon + límite de filas en las certified queries.

---

## 3. Foundry — context engineering y memoria

Aquí es donde tu repo tiene más espacio para crecer. Piénsalo en capas:

### (a) Context engineering — qué entra en cada prompt

Hoy `_genie_business_prompt` es estático. Lo que harías en producción:

1. Identity context: quién pregunta + rol + permisos. Inyectarlo en el system prompt para que el modelo no sugiera filtros que el usuario no puede ver.
2. Domain context selectivo: en vez de meter todo el glosario en el prompt, haz retrieval sobre un knowledge store (Foundry "knowledge sources" o un index propio en Azure AI Search / Cosmos) de:
   - definiciones de métricas relevantes a la pregunta,
   - sinónimos del negocio,
   - top-5 certified queries similares.

   Es RAG, pero sobre metadata semántica, no sobre documentos.
3. Dashboard state: ya lo reconstruyes en `dashboard_context.py` — eso es excelente context engineering. Mantén ese patrón.
4. Conversation summary: cuando el hilo pasa de ~10 turnos, sustituye los antiguos por un resumen estructurado (entities mencionadas, filtros aplicados, datasets cacheados). Ahorra tokens y mejora la coherencia.

### (b) Memoria — corto vs. largo plazo

- Corto plazo (ya lo tienes): `conversation_id` de Foundry. Ok.
- Medio plazo (sesión multi-turno): cachear `datasetId` + columnas en el state del LangGraph (ya lo haces con `cacheDataset`). Mantenlo.
- Largo plazo (entre sesiones): esto es lo que falta. Necesitas un store externo (Cosmos DB / Azure AI Search) con:
  - User preferences: idioma, divisa, granularidad temporal por defecto, dominio favorito.
  - Saved dashboards / pinned visuals: que el usuario diga "carga mi vista de overdue" y el agente sepa qué `addVisual` emitir.
  - Learned synonyms: cuando el usuario corrige al agente ("no, 'exposure' aquí es exposure_neta"), persistirlo a nivel de usuario o tenant.
  - Question patterns: las top-N preguntas del usuario sirven como sugerencias en la UI.

Foundry tiene Threads y la conversation API, pero la memoria cross-thread la implementas tú con un store. Patrón típico: clave `(tenantId, userId)` → JSON con preferencias + embeddings de Q&A pasadas.

### (c) Arquitectura multi-agente

Cuando crezcan dominios, evoluciona de "un LangGraph con router" a un supervisor + especialistas:

```text
Supervisor (Foundry hosted, AG-UI)
 ├─ Risk specialist     → Genie Space "risk"
 ├─ Claims specialist   → Genie Space "claims"
 ├─ Finance specialist  → Genie Space "finance"
 └─ Narrative/Insight specialist (sin Genie, solo razona sobre resultados ya cacheados)
```

Cada specialist es un prompt agent de Foundry distinto, con sus instructions y su MCP tool. El supervisor decide a quién enrutar. Esto es exactamente la extensión natural de lo que ya tienes con `risk-exposure-genie-agent`.

### (d) Evaluación y observabilidad (clave para producción)

- Define evaluation suites (placeholder ya en `agent-metadata.yaml`). Mínimo: golden set de 50-100 Q&A con ground truth (SQL esperado o métrica esperada). Ejecútalo en CI antes de promover una nueva instrucción.
- Foundry traces + App Insights ya están — añade custom dimensions por dominio enrutado, número de tool calls a Genie, latencia de Genie, hit/miss de memoria. Sin esto, no sabrás dónde degrada cuando metas más Spaces.
- Continuous evaluation sobre tráfico real (Foundry lo soporta) — detecta drift cuando un Genie Space cambia.

---

## 4. Cómo enfocarlo — orden recomendado

1. Primero el semantic layer (Databricks/UC + Genie Space). Sin esto, mejorar el agente no rinde.
2. Luego governed access: RLS/column masks + OBO en el MCP. Imprescindible para multi-tenant/roles.
3. Después memoria larga + context retrieval: Cosmos/AI Search con preferencias y glossary retrieval.
4. Después multi-Space + routing: cuando aparezca el segundo dominio, no antes.
5. En paralelo desde el principio: evals + observabilidad. No las dejes para el final.
