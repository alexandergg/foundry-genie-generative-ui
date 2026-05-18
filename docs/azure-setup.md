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
cp scripts/uc3.env.example .uc3.env.local
$EDITOR .uc3.env.local
source .uc3.env.local
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

After deployment, update `.uc3.env.local` with:

```bash
export DATABRICKS_WORKSPACE_NAME="<workspace-name>"
export DATABRICKS_HOST="https://<workspace-host>"
```

## 3. Create or reuse a Databricks SQL Warehouse

```bash
source .uc3.env.local
./scripts/10-create-warehouse.sh
```

Copy the printed `WAREHOUSE_ID` into `.uc3.env.local`.

Recommended demo settings:

- Serverless SQL if enabled, otherwise Pro SQL.
- Size: `2X-Small`.
- Min/max clusters: `1/1`.
- Auto-stop: `5-10` minutes.

## 4. Load the synthetic UC3 dataset

This step can start the SQL Warehouse.

```bash
source .uc3.env.local
ALLOW_WAREHOUSE_START=yes ./scripts/20-run-demo-sql.sh
```

The script creates demo tables and the business-facing view:

```text
${UC3_CATALOG}.${UC3_SCHEMA}.vw_uc3_genie_exposure_claims
```

## 5. Create the Databricks Genie Space

```bash
./scripts/30-create-genie-space.sh
```

Copy the printed `GENIE_SPACE_ID` into `.uc3.env.local`.

Then open the Genie Space in Databricks and add the guidance from [docs/genie-space-config.md](genie-space-config.md). Genie requires Unity Catalog data, SQL entitlement, warehouse access, and appropriate ACLs.

## 6. Prepare the Microsoft Foundry project

In Microsoft Foundry, create or select a project and deploy a model. Capture:

```bash
export FOUNDRY_PROJECT_ENDPOINT="https://<foundry-resource>.services.ai.azure.com/api/projects/<project-name>"
export FOUNDRY_PROJECT_RESOURCE_ID="/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<account>/projects/<project>"
export FOUNDRY_MODEL_DEPLOYMENT="gpt-4.1-mini"
```

Add these values to `.uc3.env.local`.

## 7. Create the Foundry RemoteTool connection and agent

```bash
source .uc3.env.local
./scripts/60-setup-foundry-genie-agent.sh
```

The script:

1. Creates or updates a Foundry `RemoteTool` project connection targeting the Databricks Genie MCP endpoint.
2. Uses `ProjectManagedIdentity` authentication with the Azure Databricks audience.
3. Creates a Foundry prompt agent version with an MCP tool.
4. Writes `.foundry/agent-metadata.yaml` for the local AG-UI bridge.

## 8. Grant Databricks permissions to the Foundry project managed identity

```bash
./scripts/50-grant-databricks-permissions.sh
```

The script grants the Foundry project managed identity:

- Databricks SQL entitlement.
- SQL Warehouse `CAN_USE`.
- Genie Space `CAN_RUN`.
- Unity Catalog `USE_CATALOG`, `USE_SCHEMA`, and `SELECT` on the UC3 objects.

## 9. Validate cloud setup without querying data

```bash
./scripts/90-validate-uc3.sh
```

This checks Databricks warehouse metadata, Genie Space metadata, and Foundry connection metadata. It does not invoke Genie.

## 10. Stop compute after setup or demo

```bash
./scripts/95-stop-compute.sh
./scripts/90-validate-uc3.sh
```
