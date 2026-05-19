---
name: azure-databricks-ops
description: Guidance for Azure, Databricks, Foundry, Bicep, SQL setup scripts, and cost-control operations in this repository. Use when changing infrastructure, setup automation, Databricks SQL assets, cloud runbooks, or operational workflows.
---

# Azure and Databricks operations

Use this skill for setup scripts, Bicep, Databricks SQL, Azure AI Foundry metadata handling, and cost-control workflows.

## Operating principles

- Treat deployments, SQL warehouse starts, and any live Azure, Databricks, or Foundry calls as explicit, user-approved operations.
- Prefer dry-run, validation, or `what-if` commands before mutations.
- Keep `.risk.env.local`, `.env*`, Foundry metadata, tenant IDs, tokens, workspace URLs, and other secrets out of git and logs.
- Preserve the human approval flow before governed Databricks data is queried.
- Keep demo data and controlled UI payloads deterministic and schema-shaped.

## Change checklist

1. Identify whether the change affects infrastructure, scripts, Databricks SQL, environment variables, docs, or runtime cloud behavior.
2. Verify script names, arguments, and environment variable names against the repository before documenting or using them.
3. Use shared shell helpers from `scripts/lib/common.sh` for Bash scripts when applicable.
4. For infrastructure changes, prefer `az deployment group what-if`; do not deploy without explicit user approval.
5. Update `README.md`, `docs/azure-setup.md`, and `docs/cost-control.md` when setup flow, script names, environment variables, or cost behavior changes.

## Validation

- Scripts/docs only: run `git diff --check` and verify referenced commands exist.
- Infrastructure: run static validation or `what-if` when credentials and approval are available.
- Do not add live cloud calls to CI or pre-commit hooks.
