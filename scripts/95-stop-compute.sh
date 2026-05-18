#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
load_local_env

require_env WAREHOUSE_ID
state="$(warehouse_state)"
if [[ "$state" == "STOPPED" ]]; then
  echo "Warehouse already stopped: $WAREHOUSE_ID"
else
  databricks_api POST "/api/2.0/sql/warehouses/$WAREHOUSE_ID/stop" >/dev/null
  echo "Stop requested for warehouse: $WAREHOUSE_ID"
fi

echo "Checking clusters and instance pools:"
databricks_api GET /api/2.0/clusters/list | python3 -c 'import json,sys; d=json.load(sys.stdin); print("clusters:", len(d.get("clusters", [])))'
databricks_api GET /api/2.0/instance-pools/list | python3 -c 'import json,sys; d=json.load(sys.stdin); print("instance_pools:", len(d.get("instance_pools", [])))'
