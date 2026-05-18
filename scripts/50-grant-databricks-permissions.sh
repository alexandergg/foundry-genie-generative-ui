#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
load_local_env

require_env FOUNDRY_PROJECT_RESOURCE_ID
require_env WAREHOUSE_ID
require_env GENIE_SPACE_ID
require_env UC3_CATALOG
UC3_SCHEMA="${UC3_SCHEMA:-default}"
UC3_VIEW_NAME="${UC3_VIEW_NAME:-vw_uc3_genie_exposure_claims}"

principal_id="$(az resource show --ids "$FOUNDRY_PROJECT_RESOURCE_ID" --api-version 2025-06-01 --query identity.principalId -o tsv)"
if [[ -z "$principal_id" || "$principal_id" == "null" ]]; then
  echo "Foundry project does not have a system-assigned managed identity." >&2
  exit 4
fi
foundry_app_id="$(az ad sp show --id "$principal_id" --query appId -o tsv)"
sp_name="foundry-project-mi-uc3-genie"

existing="$(databricks_api GET "/api/2.0/preview/scim/v2/ServicePrincipals?filter=applicationId%20eq%20%22$foundry_app_id%22" | python3 -c 'import json,sys; d=json.load(sys.stdin); print((d.get("Resources") or [{}])[0].get("id", ""))')"
if [[ -z "$existing" ]]; then
  body="$(mktemp)"
  APP_ID="$foundry_app_id" SP_NAME="$sp_name" python3 - <<'PY' > "$body"
import json, os
print(json.dumps({
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServicePrincipal"],
    "applicationId": os.environ["APP_ID"],
    "displayName": os.environ["SP_NAME"],
    "active": True,
}))
PY
  databricks_api POST /api/2.0/preview/scim/v2/ServicePrincipals "$body" | python3 -m json.tool
  rm -f "$body"
else
  echo "Databricks service principal already exists: $foundry_app_id ($existing)"
fi
existing="$(databricks_api GET "/api/2.0/preview/scim/v2/ServicePrincipals?filter=applicationId%20eq%20%22$foundry_app_id%22" | python3 -c 'import json,sys; d=json.load(sys.stdin); print((d.get("Resources") or [{}])[0].get("id", ""))')"

grant_object_permission() {
  local object_path="$1" level="$2"
  local body
  body="$(mktemp)"
  SP_ID="$foundry_app_id" PERMISSION_LEVEL="$level" python3 - <<'PY' > "$body"
import json, os
print(json.dumps({
    "access_control_list": [{
        "service_principal_name": os.environ["SP_ID"],
        "permission_level": os.environ["PERMISSION_LEVEL"],
    }]
}))
PY
  databricks_api PATCH "/api/2.0/permissions/$object_path" "$body" >/dev/null
  rm -f "$body"
  echo "Granted $level on $object_path to $foundry_app_id"
}

grant_uc_permission() {
  local type="$1" full_name="$2" privilege="$3"
  local body
  body="$(mktemp)"
  PRINCIPAL="$foundry_app_id" PRIVILEGE="$privilege" python3 - <<'PY' > "$body"
import json, os
print(json.dumps({
    "changes": [{
        "principal": os.environ["PRINCIPAL"],
        "add": [os.environ["PRIVILEGE"]],
    }]
}))
PY
  databricks_api PATCH "/api/2.1/unity-catalog/permissions/$type/$full_name" "$body" >/dev/null
  rm -f "$body"
  echo "Granted $privilege on $type $full_name to $foundry_app_id"
}

if [[ -n "$existing" ]]; then
  body="$(mktemp)"
  cat > "$body" <<'JSON'
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [{
    "op": "add",
    "path": "entitlements",
    "value": [{"value": "workspace-access"}, {"value": "databricks-sql-access"}]
  }]
}
JSON
  databricks_api PATCH "/api/2.0/preview/scim/v2/ServicePrincipals/$existing" "$body" >/dev/null || true
  rm -f "$body"
  echo "Ensured workspace and Databricks SQL entitlements for $foundry_app_id"
fi

grant_object_permission "warehouses/$WAREHOUSE_ID" CAN_USE
grant_object_permission "genie/$GENIE_SPACE_ID" CAN_RUN
grant_uc_permission catalog "$UC3_CATALOG" USE_CATALOG
grant_uc_permission schema "$UC3_CATALOG.$UC3_SCHEMA" USE_SCHEMA
for table_name in dim_broker fact_claim fact_exposure "$UC3_VIEW_NAME"; do
  grant_uc_permission table "$UC3_CATALOG.$UC3_SCHEMA.$table_name" SELECT
done
