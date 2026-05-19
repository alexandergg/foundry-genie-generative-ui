---
name: python-agent
description: Guidance for the FastAPI and LangGraph Python agent in apps/agent. Use when changing agent orchestration, Azure AI Foundry integration, Databricks Genie MCP handling, parsing, mapping, session logic, or Python tests.
---

# Python agent work

Use this skill for changes under `apps/agent`.

## Agent principles

- Keep external SDK handling isolated in small helpers.
- Prefer typed dataclasses, aliases, or explicit models for internal payloads.
- Preserve human approval before governed Databricks data is queried.
- Do not require cloud credentials for unit tests.
- Keep live Azure AI Foundry and Databricks calls opt-in and out of CI.

## Change checklist

1. Identify affected parsing, mapping, session, orchestration, or API boundaries.
2. Add or update tests before or with behavior changes.
3. Keep deterministic outputs for controlled UI component payloads.
4. Avoid broad exception swallowing; surface actionable errors without leaking secrets.
5. Update docs when environment variables, setup flow, or validation commands change.

## Validation

- Run `npm run validate:agent` after Python changes.
- If validation is blocked, report the exact command and reason.
