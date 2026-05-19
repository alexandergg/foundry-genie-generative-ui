# Contributing

## Setup

```bash
npm install
npm run install:agent
```

## Validation

```bash
npm run validate          # Python agent + frontend
npm run validate:agent    # Ruff, mypy, pytest, py_compile
npm run validate:web      # ESLint + Next.js build
```

Install pre-commit hooks after the Python agent tools are available:

```bash
python3 -m pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Safety

- Do not commit local `.env` files, `.risk.env.local`, or `.foundry/agent-metadata.yaml`.
- Do not run live Azure, Databricks, or Foundry mutation scripts without explicit intent.
- Keep README and `docs/` in sync when scripts, setup flow, or validation commands change.
