---
name: docs-runbooks
description: Guidance for maintaining README files, documentation, and operational runbooks. Use when changing setup instructions, validation commands, environment variable references, troubleshooting steps, or cost-control documentation.
---

# Docs and runbooks

Use this skill when changing `README.md`, files under `docs/`, or user-facing setup and operations guidance.

## Documentation standards

- Keep setup order explicit and copy-pasteable.
- Align command names, script paths, flags, and environment variables with the actual repository.
- Call out cost implications for Databricks SQL Warehouse usage and other cloud resources.
- Do not document real tenant-specific values, secrets, tokens, workspace URLs, or local `.env` contents.
- Prefer concise runbooks with clear prerequisites, commands, expected results, and cleanup steps.

## Change checklist

1. Confirm every referenced script, command, and file path exists.
2. Keep validation commands current with `package.json`, CI, and repository instructions.
3. Update related docs together when setup flow or command names change.
4. Preserve opt-in language for Azure, Databricks, and Foundry operations.
5. Include troubleshooting notes only when they are actionable and repository-specific.

## Validation

- Run `git diff --check` for docs and scripts changes.
- If documentation references validation scripts, verify those script names and package scripts exist.
