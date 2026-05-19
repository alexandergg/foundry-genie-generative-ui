#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
load_local_env

require_env FOUNDRY_PROJECT_RESOURCE_ID
require_env FOUNDRY_PROJECT_ENDPOINT
require_env FOUNDRY_MODEL_DEPLOYMENT
require_env DATABRICKS_HOST
require_env GENIE_SPACE_ID

export FOUNDRY_GENIE_CONNECTION_NAME="${FOUNDRY_GENIE_CONNECTION_NAME:-databricks-genie-risk-mcp}"
export FOUNDRY_GENIE_AGENT_NAME="${FOUNDRY_GENIE_AGENT_NAME:-risk-exposure-genie-agent}"
export FOUNDRY_GENIE_PROMPT_TEMPLATE="${FOUNDRY_GENIE_PROMPT_TEMPLATE:-$SCRIPT_DIR/foundry-genie-agent-instructions.txt}"
GENIE_MCP_ENDPOINT="${DATABRICKS_HOST%/}/api/2.0/mcp/genie/$GENIE_SPACE_ID"
DATABRICKS_AUDIENCE="2ff814a6-3304-4ab8-85cb-cd0e6f879c1d"

if [[ ! -f "$FOUNDRY_GENIE_PROMPT_TEMPLATE" ]]; then
  echo "Missing Foundry Genie prompt template: $FOUNDRY_GENIE_PROMPT_TEMPLATE" >&2
  exit 2
fi

connection_id="$FOUNDRY_PROJECT_RESOURCE_ID/connections/$FOUNDRY_GENIE_CONNECTION_NAME"
body="$(mktemp)"
cat > "$body" <<JSON
{
  "properties": {
    "category": "RemoteTool",
    "target": "$GENIE_MCP_ENDPOINT",
    "authType": "ProjectManagedIdentity",
    "audience": "$DATABRICKS_AUDIENCE",
    "group": "GenericProtocol",
    "useWorkspaceManagedIdentity": false,
    "isSharedToAll": false,
    "metadata": {
      "ApiType": "Azure",
      "workspace-hostname": "${DATABRICKS_HOST#https://}",
      "genie_space_id": "$GENIE_SPACE_ID"
    }
  }
}
JSON
az rest --method put --url "https://management.azure.com${connection_id}?api-version=2025-06-01" --body @"$body" -o none
rm -f "$body"
echo "Created/updated Foundry RemoteTool connection: $FOUNDRY_GENIE_CONNECTION_NAME"

venv_dir="${FOUNDRY_SDK_VENV:-$DEMO_ROOT/.venv-foundry-genie}"
if [[ ! -x "$venv_dir/bin/python" ]]; then
  python3 -m venv "$venv_dir"
  "$venv_dir/bin/python" -m pip install --quiet --upgrade pip
  "$venv_dir/bin/python" -m pip install --quiet --pre azure-ai-projects azure-identity
fi

"$venv_dir/bin/python" - <<'PY'
import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

endpoint=os.environ['FOUNDRY_PROJECT_ENDPOINT']
agent_name=os.environ.get('FOUNDRY_GENIE_AGENT_NAME','risk-exposure-genie-agent')
model=os.environ['FOUNDRY_MODEL_DEPLOYMENT']
connection=os.environ.get('FOUNDRY_GENIE_CONNECTION_NAME','databricks-genie-risk-mcp')
genie_space_id=os.environ['GENIE_SPACE_ID']
genie_endpoint=os.environ['DATABRICKS_HOST'].rstrip('/') + '/api/2.0/mcp/genie/' + genie_space_id
warehouse=os.environ.get('WAREHOUSE_NAME','Risk Exposure Genie Demo 2X-Small')
prompt_template=Path(os.environ['FOUNDRY_GENIE_PROMPT_TEMPLATE'])
view_name=os.environ.get('DEMO_VIEW_NAME','vw_risk_genie_exposure_claims')
catalog=os.environ.get('DEMO_CATALOG','').strip()
schema=os.environ.get('DEMO_SCHEMA','default').strip()
preferred_view='.'.join(part for part in [catalog, schema, view_name] if part)
instructions=prompt_template.read_text(encoding='utf-8').format(
    preferred_view=preferred_view,
    preferred_view_short=view_name,
    warehouse=warehouse,
)
client=AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())

definition={
    'kind': 'prompt',
    'model': model,
    'instructions': instructions,
    'temperature': 0.2,
    'tools': [{
        'type': 'mcp',
        'server_label': 'databricks-genie-risk',
        'server_url': genie_endpoint,
        'require_approval': 'always',
        'project_connection_id': connection,
    }],
}
created=client.agents.create_version(
    agent_name,
    definition=definition,
    description='Foundry agent for querying a Databricks Genie Space with manual SQL Warehouse cost control.',
    metadata={'use_case':'risk-databricks-genie','genie_space_id':genie_space_id,'mcp_connection':connection,'warehouse':warehouse},
)
print(created)
PY

mkdir -p "$DEMO_ROOT/.foundry"
cat > "$DEMO_ROOT/.foundry/agent-metadata.yaml" <<YAML
defaultEnvironment: dev
environments:
  dev:
    projectEndpoint: $FOUNDRY_PROJECT_ENDPOINT
    agentName: $FOUNDRY_GENIE_AGENT_NAME
    model: $FOUNDRY_MODEL_DEPLOYMENT
    databricksGenieMcpEndpoint: $GENIE_MCP_ENDPOINT
    databricksGenieProjectConnectionName: $FOUNDRY_GENIE_CONNECTION_NAME
    databricksGenieSpaceId: $GENIE_SPACE_ID
    databricksSqlWarehouseName: ${WAREHOUSE_NAME:-Risk Exposure Genie Demo 2X-Small}
    evaluationSuites: []
YAML

echo "Wrote .foundry/agent-metadata.yaml for the local AG-UI bridge."
