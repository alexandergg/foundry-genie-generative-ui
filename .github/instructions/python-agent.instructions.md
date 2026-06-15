---
applyTo: "apps/*/agent/**/*.py,apps/*/agent/pyproject.toml"
---

# Python agent instructions

- Keep FastAPI/LangGraph behavior deterministic and testable.
- Treat Azure AI Foundry and OpenAI response objects as external SDK boundaries; narrow with helpers before using values.
- Use Ruff formatting and linting; do not hand-format against Ruff.
- Add or update pytest tests for parsing, component mapping, session-cache behavior, and settings changes.
- Do not add live Azure, Databricks, or Foundry calls to unit tests.
- Keep broad `Any` limited to SDK responses or JSON-like component payloads.
