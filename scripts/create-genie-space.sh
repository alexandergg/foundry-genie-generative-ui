#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
load_local_env

require_env WAREHOUSE_ID
export GENIE_SPACE_TITLE="${GENIE_SPACE_TITLE:-Risk Exposure Genie Demo}"
export GENIE_SPACE_DESCRIPTION="${GENIE_SPACE_DESCRIPTION:-Genie Space for conversational analytics over synthetic exposure, overdue balance, claims, and broker data for the Risk Exposure Generative UI demo.}"

existing_id="$(databricks_api GET /api/2.0/genie/spaces | python3 -c 'import json,os,sys; title=os.environ["GENIE_SPACE_TITLE"]; d=json.load(sys.stdin); print(next((s.get("space_id","") for s in d.get("spaces",[]) if s.get("title")==title), ""))')"
if [[ -n "$existing_id" ]]; then
  echo "Genie Space already exists: $GENIE_SPACE_TITLE"
  echo "export GENIE_SPACE_ID=\"$existing_id\""
  echo "export DATABRICKS_GENIE_MCP_ENDPOINT=\"${DATABRICKS_HOST%/}/api/2.0/mcp/genie/$existing_id\""
  exit 0
fi

body="$(mktemp)"
cat > "$body" <<JSON
{
  "title": "$GENIE_SPACE_TITLE",
  "description": "$GENIE_SPACE_DESCRIPTION",
  "warehouse_id": "$WAREHOUSE_ID"
}
JSON

response="$(databricks_api POST /api/2.0/genie/spaces "$body")"
rm -f "$body"
echo "$response" | python3 -m json.tool
space_id="$(echo "$response" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("space_id", ""))')"
if [[ -n "$space_id" ]]; then
  echo "export GENIE_SPACE_ID=\"$space_id\""
  echo "export DATABRICKS_GENIE_MCP_ENDPOINT=\"${DATABRICKS_HOST%/}/api/2.0/mcp/genie/$space_id\""
fi
