#!/usr/bin/env bash
set -euo pipefail

: "${DATABRICKS_HOST:?Set DATABRICKS_HOST, e.g. https://adb-...azuredatabricks.net}"
: "${DATABRICKS_TOKEN:?Set DATABRICKS_TOKEN with a Databricks PAT or OAuth token}"
ACTION="${1:-status}"
WAREHOUSE_ID="${WAREHOUSE_ID:-}"

api() {
  local method="$1"
  local path="$2"
  curl -fsS -X "$method" \
    -H "Authorization: Bearer $DATABRICKS_TOKEN" \
    -H "Content-Type: application/json" \
    "$DATABRICKS_HOST$path"
}

case "$ACTION" in
  list)
    api GET "/api/2.0/sql/warehouses" ;;
  status)
    : "${WAREHOUSE_ID:?Set WAREHOUSE_ID or run '$0 list'}"
    api GET "/api/2.0/sql/warehouses/$WAREHOUSE_ID" ;;
  start)
    : "${WAREHOUSE_ID:?Set WAREHOUSE_ID or run '$0 list'}"
    api POST "/api/2.0/sql/warehouses/$WAREHOUSE_ID/start" ;;
  stop)
    : "${WAREHOUSE_ID:?Set WAREHOUSE_ID or run '$0 list'}"
    api POST "/api/2.0/sql/warehouses/$WAREHOUSE_ID/stop" ;;
  *)
    echo "Usage: $0 list|status|start|stop" >&2
    exit 2 ;;
esac
