# Contributing

Thanks for considering a contribution. This repository is a public demo of Generative UI on Microsoft Foundry + Databricks Genie. It is not a production product, but we try to keep it close to how a real team would run it.

## Repository layout

```
apps/controlled/agent     Python LangGraph agent, served as a Foundry hosted agent
apps/controlled/web       Next.js 15 frontend, CopilotKit + AG-UI surface
infra/         Bicep modules (foundry, identity, RBAC, monitoring, ACR, etc.)
scripts/       Setup, validate, and deploy helpers
docs/          Architecture, demo script, Azure setup, cost control
databricks/    Genie space SQL and warehouse helpers
```

For agent-specific or web-specific conventions, see `.github/instructions/*.md` and `AGENTS.md`.

## Setup

```bash
npm install
npm run install:controlled-agent
```

`install:controlled-agent` creates `apps/controlled/agent/.venv` with Python 3.12 and installs the editable agent package plus the `[dev]` extras (ruff, mypy, pytest, pre-commit).

Then enable pre-commit:

```bash
python3 -m pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Pre-commit runs `detect-private-key`, `ruff format`, `ruff check`, and a quick `py_compile` sanity pass.

## Branching

- `main` is always shippable and protected. CI must be green to merge.
- Use short, descriptive branch names: `feat/dashboard-grid`, `fix/genie-429-retry`, `docs/changelog`.
- Rebase or merge `main` into your branch before opening a PR to avoid stale conflicts.

## Commit conventions

This repo uses [Conventional Commits](https://www.conventionalcommits.org/). The CHANGELOG is built by re-grouping these into Keep a Changelog categories at release time.

Allowed types we have used in this repo:

| Type | When to use |
| ---- | ----------- |
| `feat` | New user-visible capability. |
| `fix` | Bug fix in shipped behavior. |
| `refactor` | Code restructuring with no functional change. |
| `chore` | Tooling, CI, gitignore, deps, repo hygiene. |
| `docs` | Documentation only. |
| `test` | Tests only. |
| `style` | Pure formatting or visual styling (CSS, ruff format), no logic change. |

Optional scope is the affected area: `feat(web): …`, `fix(agent): …`, `chore(ci): …`, `refactor(infra): …`.

Keep the subject under ~72 characters, present tense, no trailing period.

## Pull request workflow

1. Open a PR against `main`. The PR template will populate automatically.
2. Fill in the **Summary**, tick the **Type of change** and **Affected area** boxes, and complete the **Checklist**.
3. CI runs:
   - `validate` (agent + web): `ruff`, `mypy`, `pytest`, ESLint, Vitest, `next build`.
   - `bicep`: `az bicep build infra/main.bicep`.
   - `markdown-lint`: informational while existing docs stabilize.
4. The default `CODEOWNERS` entry auto-requests a maintainer review.
5. Squash-merge once the checklist is green. The PR title becomes the squash commit subject, so it should already follow Conventional Commits.

## Validation

```bash
npm run validate          # Agent + web. Run this before opening a PR.
npm run validate:controlled-agent    # Ruff format check, ruff lint, mypy strict, pytest, py_compile.
npm run validate:controlled-web      # ESLint + Vitest + next build.
```

If you touch infrastructure, also run:

```bash
az bicep build --file infra/main.bicep
```

## Testing expectations

- New agent code paths in `apps/controlled/agent/foundry_genie_generative_ui/` should ship with a `pytest` covering the happy path and at least one failure mode. See `apps/controlled/agent/tests/` for examples.
- New pure-logic helpers in `apps/controlled/web/src/` should ship with a Vitest. Avoid UI snapshot tests; prefer asserting on shape and routing.
- Live Azure / Databricks / Foundry mutation scripts are not covered by CI. If you change them, run them manually against a sandbox subscription and note the result in the PR.

## Safety

- Do not commit `.env*`, `.risk.env.local`, `.foundry/agent-metadata.yaml`, or anything under `.azure/`. They are gitignored by default — please do not unignore them.
- Do not commit local agent permissions or tool allowlists. `.claude/` is gitignored.
- Do not run live Azure, Databricks, or Foundry mutation scripts (`deploy-infra.sh`, `setup-foundry-genie-agent.sh`, `delete-resources.sh`, `databricks-warehouse.sh`, `run-demo-sql.sh`) without explicit intent and a known target.
- Keep `README.md`, `docs/`, and `AGENTS.md` in sync when scripts, setup flow, or validation commands change.

## Reporting issues

- Bugs and feature requests: use the templates under `.github/ISSUE_TEMPLATE/`.
- Security vulnerabilities: do not open a public issue. See [SECURITY.md](SECURITY.md) for the private reporting flow via GitHub Security Advisories.
- Foundry / Azure platform issues belong upstream at [MSRC](https://msrc.microsoft.com/). Databricks issues belong upstream at [Databricks Security](https://www.databricks.com/legal/security).
