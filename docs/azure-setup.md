# Azure, Databricks, Genie, and Microsoft Foundry setup

This runbook prepares the live cloud side of the demo.

## 0. Prerequisites

- Azure CLI authenticated with `az login`.
- Permission to create a resource group and deploy Azure Databricks.
- Access to a Microsoft Foundry project with a model deployment such as `gpt-4.1-mini`, or permission to create one in the Foundry portal.
- Databricks workspace admin or equivalent permissions for SQL Warehouses, Genie Spaces, service principals, and Unity Catalog grants.
- Python 3.10+ and Bash.

Official references:

- Databricks Genie setup: <https://learn.microsoft.com/azure/databricks/genie/set-up>
- Genie API requirements: <https://learn.microsoft.com/azure/databricks/genie/conversation-api>
- Foundry MCP tools: <https://learn.microsoft.com/azure/foundry/agents/how-to/tools/model-context-protocol>

## 1. Configure local deployment variables

```bash
cp scripts/risk.env.example .risk.env.local
$EDITOR .risk.env.local
source .risk.env.local
```

Minimum values before infrastructure deployment:

- `AZURE_SUBSCRIPTION_ID`
- `AZURE_TENANT_ID`
- `LOCATION`
- `RESOURCE_GROUP`

## 2. Deploy Azure infrastructure

```bash
./scripts/preflight.sh
./scripts/deploy-infra.sh
```

The Bicep deployment creates:

- Azure Databricks workspace.
- ADLS Gen2 storage account for demo/data readiness.
- Log Analytics workspace.

It intentionally does not create Databricks data-plane objects such as SQL Warehouses or Genie Spaces.

After deployment, update `.risk.env.local` with:

```bash
export DATABRICKS_WORKSPACE_NAME="<workspace-name>"
export DATABRICKS_HOST="https://<workspace-host>"
```

## 3. Create or reuse a Databricks SQL Warehouse

```bash
source .risk.env.local
./scripts/create-warehouse.sh
```

Copy the printed `WAREHOUSE_ID` into `.risk.env.local`.

Recommended demo settings:

- Serverless SQL if enabled, otherwise Pro SQL.
- Size: `2X-Small`.
- Min/max clusters: `1/1`.
- Auto-stop: `5-10` minutes.

## 4. Load the synthetic Risk Exposure dataset

This step can start the SQL Warehouse.

```bash
source .risk.env.local
ALLOW_WAREHOUSE_START=yes ./scripts/run-demo-sql.sh
```

The script creates demo tables and the business-facing view:

```text
${DEMO_CATALOG}.${DEMO_SCHEMA}.vw_risk_genie_exposure_claims
```

## 5. Create the Databricks Genie Space

```bash
./scripts/create-genie-space.sh
```

Copy the printed `GENIE_SPACE_ID` into `.risk.env.local`.

Then open the Genie Space in Databricks and add the guidance from [docs/genie-space-config.md](genie-space-config.md). Genie requires Unity Catalog data, SQL entitlement, warehouse access, and appropriate ACLs.

## 6. Prepare the Microsoft Foundry project

In Microsoft Foundry, create or select a project and deploy a model. Capture:

```bash
export FOUNDRY_PROJECT_ENDPOINT="https://<foundry-resource>.services.ai.azure.com/api/projects/<project-name>"
export FOUNDRY_PROJECT_RESOURCE_ID="/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<account>/projects/<project>"
export FOUNDRY_MODEL_DEPLOYMENT="gpt-4.1-mini"
```

Add these values to `.risk.env.local`.

## 7. Create the Foundry RemoteTool connection and agent

```bash
source .risk.env.local
./scripts/setup-foundry-genie-agent.sh
```

The script:

1. Creates or updates a Foundry `RemoteTool` project connection targeting the Databricks Genie MCP endpoint.
2. Uses `ProjectManagedIdentity` authentication with the Azure Databricks audience.
3. Creates a Foundry prompt agent version with an MCP tool and the instructions from `scripts/foundry-genie-agent-instructions.txt`.
4. Writes `.foundry/agent-metadata.yaml` for the local AG-UI bridge.

## 8. Grant Databricks permissions to the Foundry project managed identity

```bash
./scripts/grant-databricks-permissions.sh
```

The script grants the Foundry project managed identity:

- Databricks SQL entitlement.
- SQL Warehouse `CAN_USE`.
- Genie Space `CAN_RUN`.
- Unity Catalog `USE_CATALOG`, `USE_SCHEMA`, and `SELECT` on the Risk Exposure objects.

## 9. Validate cloud setup without querying data

```bash
./scripts/validate-risk.sh
```

This checks Databricks warehouse metadata, Genie Space metadata, and Foundry connection metadata. It does not invoke Genie.

## 10. Stop compute after setup or demo

```bash
./scripts/stop-compute.sh
./scripts/validate-risk.sh
```
