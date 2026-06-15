#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Usage: validate-agent.sh [agent-dir] [--quick]
# agent-dir is relative to the repo root and defaults to the controlled agent.
AGENT_SUBDIR="apps/controlled/agent"
QUICK=0
for arg in "$@"; do
  case "$arg" in
    --quick) QUICK=1 ;;
    *) AGENT_SUBDIR="$arg" ;;
  esac
done

AGENT_DIR="$ROOT_DIR/$AGENT_SUBDIR"
PYTHON_BIN="${PYTHON:-python3}"

if [[ -x "$AGENT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$AGENT_DIR/.venv/bin/python"
fi

cd "$AGENT_DIR"

PY_TARGETS=(main.py src tests)
if [[ -f hosted_main.py ]]; then
  PY_TARGETS+=(hosted_main.py)
fi

"$PYTHON_BIN" -m ruff format --check .
"$PYTHON_BIN" -m ruff check .

if [[ "$QUICK" -eq 1 ]]; then
  "$PYTHON_BIN" -m pytest tests
  exit 0
fi

"$PYTHON_BIN" -m mypy "${PY_TARGETS[@]}"
"$PYTHON_BIN" -m pytest tests
"$PYTHON_BIN" -m py_compile main.py
if [[ -f hosted_main.py ]]; then
  "$PYTHON_BIN" -m py_compile hosted_main.py
fi
"$PYTHON_BIN" -m compileall -q src
