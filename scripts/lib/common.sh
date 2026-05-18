#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UC3_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

load_local_env() {
  if [[ -f "$UC3_ROOT/.uc3.env.local" ]]; then
    # shellcheck disable=SC1091
    source "$UC3_ROOT/.uc3.env.local"
  fi
}

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: $name" >&2
    exit 2
  fi
}

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'
}

databricks_token() {
  if [[ -n "${DATABRICKS_TOKEN:-}" ]]; then
    printf '%s' "$DATABRICKS_TOKEN"
  else
    az account get-access-token \
      --resource 2ff814a6-3304-4ab8-85cb-cd0e6f879c1d \
      --query accessToken -o tsv
  fi
}

databricks_api() {
  local method="$1"
  local path="$2"
  local body_file="${3:-}"
  require_env DATABRICKS_HOST
  local token
  token="$(databricks_token)"
  if [[ -n "$body_file" ]]; then
    curl -fsS -X "$method" \
      -H "Authorization: Bearer $token" \
      -H "Content-Type: application/json" \
      --data @"$body_file" \
      "$DATABRICKS_HOST$path"
  else
    curl -fsS -X "$method" \
      -H "Authorization: Bearer $token" \
      -H "Content-Type: application/json" \
      "$DATABRICKS_HOST$path"
  fi
}

warehouse_state() {
  require_env WAREHOUSE_ID
  databricks_api GET "/api/2.0/sql/warehouses/$WAREHOUSE_ID" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("state","UNKNOWN"))'
}

foundry_account_resource_id() {
  require_env FOUNDRY_PROJECT_RESOURCE_ID
  python3 - <<'PY'
import os
rid=os.environ['FOUNDRY_PROJECT_RESOURCE_ID']
marker='/projects/'
if marker not in rid:
    raise SystemExit('FOUNDRY_PROJECT_RESOURCE_ID must include /projects/<name>')
print(rid.split(marker,1)[0])
PY
}
