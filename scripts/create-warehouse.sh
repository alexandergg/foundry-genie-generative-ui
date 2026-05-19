#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
load_local_env

export WAREHOUSE_NAME="${WAREHOUSE_NAME:-Risk Exposure Genie Demo 2X-Small}"
export WAREHOUSE_SIZE="${WAREHOUSE_SIZE:-2X-Small}"
export WAREHOUSE_AUTO_STOP_MINUTES="${WAREHOUSE_AUTO_STOP_MINUTES:-10}"

existing_id="$(databricks_api GET /api/2.0/sql/warehouses | python3 -c 'import json,os,sys; name=os.environ["WAREHOUSE_NAME"]; d=json.load(sys.stdin); print(next((w["id"] for w in d.get("warehouses",[]) if w.get("name")==name), ""))')"
if [[ -n "$existing_id" ]]; then
  echo "Warehouse already exists: $WAREHOUSE_NAME"
  echo "export WAREHOUSE_ID=\"$existing_id\""
  exit 0
fi

body="$(mktemp)"
cat > "$body" <<JSON
{
  "name": "$WAREHOUSE_NAME",
  "cluster_size": "$WAREHOUSE_SIZE",
  "min_num_clusters": 1,
  "max_num_clusters": 1,
  "auto_stop_mins": $WAREHOUSE_AUTO_STOP_MINUTES,
  "enable_serverless_compute": true,
  "warehouse_type": "PRO"
}
JSON

response="$(databricks_api POST /api/2.0/sql/warehouses "$body")"
rm -f "$body"
echo "$response" | python3 -m json.tool
warehouse_id="$(echo "$response" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("id", ""))')"
if [[ -n "$warehouse_id" ]]; then
  echo "export WAREHOUSE_ID=\"$warehouse_id\""
fi
