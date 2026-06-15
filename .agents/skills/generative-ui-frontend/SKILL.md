---
name: generative-ui-frontend
description: Guidance for the Next.js generative UI frontends in apps/*/web. Use when changing React components, CopilotKit or AG-UI integration, Recharts visualizations, frontend API routes, styling, or TypeScript UI logic.
---

# Generative UI frontend

Use this skill for changes under `apps/*/web` (the controlled, declarative, and open-ended frontends).

## Frontend principles

- Keep CopilotKit runtime usage centralized through `/api/copilotkit` unless the user explicitly requests an architecture change.
- Keep generative UI components controlled by explicit, typed props.
- Prefer deterministic chart data mapping and clear fallback UI for missing or incomplete data.
- Avoid unnecessary `any`; keep component props and API payloads typed.
- Do not add hidden live cloud calls from frontend code.

## Change checklist

1. Identify affected components, hooks, API routes, types, and tests.
2. Preserve existing user approval and governed-data flows.
3. Keep Recharts payloads schema-shaped and stable across renders.
4. Prefer small helpers for mapping/parsing instead of broad inline fallbacks.
5. Update docs only when setup, behavior, commands, or environment variables change.

## Validation

- Run `npm run validate:<band>-web` after frontend changes (`<band>` = controlled | declarative | open-ended).
- If validation is blocked, report the exact command and reason.
