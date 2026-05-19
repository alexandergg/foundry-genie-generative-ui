# Repo validation

Use this skill when preparing or reviewing changes.

1. Identify touched surfaces: Python agent, frontend, scripts/docs, infra, or data SQL.
2. Run the narrow validation first:
   - Python: `npm run validate:agent`
   - Frontend: `npm run validate:web`
   - Full repo: `npm run validate`
   - Docs/scripts only: `git diff --check`
3. Do not run live Azure/Databricks/Foundry commands unless the user explicitly asks.
4. Report exact commands run and any blocked checks.
