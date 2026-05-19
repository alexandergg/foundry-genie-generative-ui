---
applyTo: "apps/web/**/*.{ts,tsx,css},apps/web/package.json"
---

# Frontend instructions

- The frontend renders controlled CopilotKit/AG-UI components for risk analytics.
- Keep component prop types explicit and shared through `apps/web/src/components/generative-ui/types.ts` where useful.
- Preserve accessible labels, readable empty states, and deterministic rendering.
- Do not bypass `/api/copilotkit` for agent calls.
- Run `npm run validate:web` after frontend changes.
