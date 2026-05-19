#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
AGENT_DIR="$ROOT_DIR/apps/agent"
PYTHON_BIN="${PYTHON:-python3}"

if [[ -x "$AGENT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$AGENT_DIR/.venv/bin/python"
fi

cd "$AGENT_DIR"

if [[ "${1:-}" == "--quick" ]]; then
  "$PYTHON_BIN" -m ruff format --check .
  "$PYTHON_BIN" -m ruff check .
  "$PYTHON_BIN" -m pytest tests
  exit 0
fi

"$PYTHON_BIN" -m ruff format --check .
"$PYTHON_BIN" -m ruff check .
"$PYTHON_BIN" -m mypy main.py src tests
"$PYTHON_BIN" -m pytest tests
"$PYTHON_BIN" -m py_compile main.py src/config.py src/foundry_agent_client.py src/session_context.py src/visualization_mapper.py
