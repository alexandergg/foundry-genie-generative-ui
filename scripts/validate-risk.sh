#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
load_local_env

require_env DATABRICKS_HOST

echo "Databricks host: $DATABRICKS_HOST"
echo "Warehouses:"
databricks_api GET /api/2.0/sql/warehouses | python3 -c 'import json,sys; d=json.load(sys.stdin); [print("- {} {} {}".format(w.get("id"), w.get("name"), w.get("state"))) for w in d.get("warehouses", [])]'

if [[ -n "${GENIE_SPACE_ID:-}" ]]; then
  echo "Genie Space:"
  databricks_api GET "/api/2.0/genie/spaces/$GENIE_SPACE_ID" | python3 -m json.tool
fi

if [[ -n "${FOUNDRY_PROJECT_RESOURCE_ID:-}" && -n "${FOUNDRY_GENIE_CONNECTION_NAME:-}" ]]; then
  echo "Foundry connection:"
  az rest --method get \
    --url "https://management.azure.com${FOUNDRY_PROJECT_RESOURCE_ID}/connections/${FOUNDRY_GENIE_CONNECTION_NAME}?api-version=2025-06-01" \
    --query '{name:name,category:properties.category,authType:properties.authType,target:properties.target,audience:properties.audience}' -o json
fi

echo "Validation completed without invoking Genie. If the warehouse is STOPPED, cost is minimized."
