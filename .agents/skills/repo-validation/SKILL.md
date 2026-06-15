---
name: repo-validation
description: Guidance for selecting and reporting repository validation commands. Use when preparing changes for review, checking quality, deciding which tests to run, or summarizing validation results.
---

# Repo validation

Use this skill when preparing or reviewing changes.

## Validation process

1. Identify touched surfaces: Python agent, frontend, scripts/docs, infrastructure, or Databricks SQL.
2. Run the narrowest relevant validation first:
   - Python agent (one band): `npm run validate:<band>-agent` (`<band>` = controlled | declarative | open-ended)
   - Frontend (one band): `npm run validate:<band>-web`
   - Full repository (all bands): `npm run validate`
   - Docs/scripts only: `git diff --check`
3. Do not run live Azure, Databricks, or Foundry commands unless the user explicitly asks and required credentials are available.
4. If a validation command fails, inspect the failure before deciding whether code changes are needed.
5. Report exact commands run, results, and any blocked checks.

## Best practices

- Prefer existing package scripts and repository tooling over adding new validation tools.
- Keep validation output concise; include detailed failure context only when it helps the user act.
- Do not treat unrelated pre-existing failures as fixed unless you changed and verified them.
