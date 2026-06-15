# Documentation index

Three demos, one per Generative UI band — each band folder under `apps/` has its own README with run instructions and key files.

## Getting started

- [local-development.md](local-development.md) — local runbook for the controlled (Genie) demo: env files, Azure CLI auth, the two runtime paths (local bridge vs Hosted Agent).
- Band quick starts: [apps/controlled/README.md](../apps/controlled/README.md) · [apps/declarative/README.md](../apps/declarative/README.md) · [apps/open-ended/README.md](../apps/open-ended/README.md)

## Concepts

- [generative-ui-spectrum.md](generative-ui-spectrum.md) — the three bands (Controlled / Declarative / Open-Ended), AG-UI vs A2UI, band-by-band mechanics, governance trade-offs, version pins.
- [architecture.md](architecture.md) — runtime flow of the controlled demo, design choices, observability.
- [generative-ui-architecture.drawio](generative-ui-architecture.drawio) — editable diagrams.net source for the architecture diagrams.

## Azure & deployment

- [azure-setup.md](azure-setup.md) — cloud foundation end to end: Foundry project/model, Key Vault, ACR, prompt agent, Hosted Agent, optional frontend App Service.
- [deploying-the-spectrum.md](deploying-the-spectrum.md) — taking all three demos to Azure: one hosted agent + one App Service per band, spectrum nav URLs, RBAC.
- [genie-space-config.md](genie-space-config.md) — Databricks Genie Space configuration for the governed dataset.
- [cost-control.md](cost-control.md) — stopping compute after sessions (`scripts/stop-compute.sh`).

## Presenting

- [session-guide.es.md](session-guide.es.md) — guion de sesión (ES): tiempos, prompts por demo, qué señalar en pantalla y fallbacks.
- [demo-script.md](demo-script.md) — guided walkthrough of the controlled (Genie) demo.

## Production

- [scaling-to-production.md](scaling-to-production.md) — qué escala y qué no (ES): capa semántica primero, acceso gobernado, memoria, multi-Space.
