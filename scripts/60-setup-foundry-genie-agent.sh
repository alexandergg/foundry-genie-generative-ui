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

export FOUNDRY_GENIE_CONNECTION_NAME="${FOUNDRY_GENIE_CONNECTION_NAME:-databricks-genie-uc3-mcp}"
export FOUNDRY_GENIE_AGENT_NAME="${FOUNDRY_GENIE_AGENT_NAME:-risk-exposure-genie-agent}"
GENIE_MCP_ENDPOINT="${DATABRICKS_HOST%/}/api/2.0/mcp/genie/$GENIE_SPACE_ID"
DATABRICKS_AUDIENCE="2ff814a6-3304-4ab8-85cb-cd0e6f879c1d"

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

venv_dir="${FOUNDRY_SDK_VENV:-$UC3_ROOT/.venv-foundry-genie}"
if [[ ! -x "$venv_dir/bin/python" ]]; then
  python3 -m venv "$venv_dir"
  "$venv_dir/bin/python" -m pip install --quiet --upgrade pip
  "$venv_dir/bin/python" -m pip install --quiet --pre azure-ai-projects azure-identity
fi

"$venv_dir/bin/python" - <<'PY'
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

endpoint=os.environ['FOUNDRY_PROJECT_ENDPOINT']
agent_name=os.environ.get('FOUNDRY_GENIE_AGENT_NAME','risk-exposure-genie-agent')
model=os.environ['FOUNDRY_MODEL_DEPLOYMENT']
connection=os.environ.get('FOUNDRY_GENIE_CONNECTION_NAME','databricks-genie-uc3-mcp')
genie_space_id=os.environ['GENIE_SPACE_ID']
genie_endpoint=os.environ['DATABRICKS_HOST'].rstrip('/') + '/api/2.0/mcp/genie/' + genie_space_id
warehouse=os.environ.get('WAREHOUSE_NAME','UC3 Genie Demo 2X-Small')
client=AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())

definition={
    'kind': 'prompt',
    'model': model,
    'instructions': f'''You are the UC3 conversational analytics agent for the Risk & Exposure Intelligence Copilot demo.

Use Azure Databricks Genie only when the user asks about exposure, overdue balances, claims, brokers, countries, product lines, legal entities, quarters, or other metrics available in the UC3 Genie Space.

The Genie MCP tool expects natural-language questions. Do not send SQL, do not invent table or column names, and do not use generic tables such as claims. To guide Genie, prefer the business-facing view vw_uc3_genie_exposure_claims, which contains: fiscal_quarter, country, legal_entity, risk_class, product_line, broker_segment, broker_name, policy_count, total_exposure_eur, total_overdue_balance_eur, total_claim_amount_eur, and claim_count.

Example: for brokers with the highest claim amount, ask Genie in natural language: "Using vw_uc3_genie_exposure_claims, show the top 10 broker_name values by total_claim_amount_eur."

If Genie cannot answer because the SQL Warehouse is stopped, tell the user to start the SQL Warehouse "{warehouse}" and retry. Never invent figures.

Always answer in English. Return business summaries, filters, assumptions, and a markdown table with stable numeric columns whenever aggregated metrics are available.''',
    'temperature': 0.2,
    'tools': [{
        'type': 'mcp',
        'server_label': 'databricks-genie-uc3',
        'server_url': genie_endpoint,
        'require_approval': 'always',
        'project_connection_id': connection,
    }],
}
created=client.agents.create_version(
    agent_name,
    definition=definition,
    description='Foundry agent for querying a Databricks Genie Space with manual SQL Warehouse cost control.',
    metadata={'use_case':'uc3-databricks-genie','genie_space_id':genie_space_id,'mcp_connection':connection,'warehouse':warehouse},
)
print(created)
PY

mkdir -p "$UC3_ROOT/.foundry"
cat > "$UC3_ROOT/.foundry/agent-metadata.yaml" <<YAML
defaultEnvironment: dev
environments:
  dev:
    projectEndpoint: $FOUNDRY_PROJECT_ENDPOINT
    agentName: $FOUNDRY_GENIE_AGENT_NAME
    model: $FOUNDRY_MODEL_DEPLOYMENT
    databricksGenieMcpEndpoint: $GENIE_MCP_ENDPOINT
    databricksGenieProjectConnectionName: $FOUNDRY_GENIE_CONNECTION_NAME
    databricksGenieSpaceId: $GENIE_SPACE_ID
    databricksSqlWarehouseName: ${WAREHOUSE_NAME:-UC3 Genie Demo 2X-Small}
    evaluationSuites: []
YAML

echo "Wrote .foundry/agent-metadata.yaml for the local AG-UI bridge."
