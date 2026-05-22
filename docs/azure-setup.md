# Azure, Databricks, Genie, and Microsoft Foundry setup

This runbook prepares the live cloud side of the demo. The frontend can run locally, but the demo needs cloud agents: the Foundry prompt Genie agent is required for data-backed answers, and the Foundry Hosted Agent is the recommended runtime when you want to run only the frontend on your machine.

Minimum path to use the local frontend:

1. Complete steps 1-9 to create the Foundry prompt agent and validate the Databricks/Genie connection.
2. Complete step 10 to deploy the AG-UI runtime as a Foundry Hosted Agent.
3. Configure `apps/web/.env.local` with the hosted Invocations endpoint as shown in [local-development.md](local-development.md#run-frontend-locally-with-the-hosted-agent).

## 0. Prerequisites

- Azure CLI authenticated with `az login`.
- Permission to create a resource group and deploy Azure Databricks, Microsoft Foundry, Key Vault, Azure Container Registry, Log Analytics, Application Insights, and optionally Azure App Service for the frontend.
- Permission to create Azure RBAC role assignments at the deployment scope. Use `Role Based Access Control Administrator` or `User Access Administrator` for least privilege; `Owner` also works but is broader.
- Foundry developer permissions to create project connections and agent versions. `Foundry User` is enough for development actions; use `Foundry Project Manager` only when you also need to invite/manage project collaborators.
- Foundry/OpenAI model quota for a deployment such as `gpt-5.4`, or an existing deployment you can reference if you disable model creation in Bicep.
- Databricks workspace admin or equivalent permissions for SQL Warehouses, Genie Spaces, service principals, entitlements, and Unity Catalog grants.
- Python 3.10+ and Bash.

The IaC assigns runtime RBAC for the managed identities it creates:

| Identity | Azure scope | Role |
| --- | --- | --- |
| App/agent user-assigned managed identity | Foundry AI Services account | `Cognitive Services OpenAI User` and `Cognitive Services User` |
| App/agent user-assigned managed identity | Key Vault | `Key Vault Secrets User` |
| App/agent user-assigned managed identity | Azure Container Registry | `Container Registry Repository Reader` and `Container Registry Repository Catalog Lister` |
| Foundry project system-assigned managed identity | Azure Container Registry | `Container Registry Repository Reader` |
| Foundry project system-assigned managed identity | Key Vault | `Key Vault Secrets User` |

Operators who query traces also need `Log Analytics Reader` or equivalent monitoring read access on the connected workspace/Application Insights resource.

The Databricks grants for Genie cannot be expressed in Azure RBAC/Bicep. They are applied later by `scripts/grant-databricks-permissions.sh` to the **Foundry project managed identity** used by the `ProjectManagedIdentity` RemoteTool connection.

Official references:

- Databricks Genie setup: <https://learn.microsoft.com/azure/databricks/genie/set-up>
- Genie API requirements: <https://learn.microsoft.com/azure/databricks/genie/conversation-api>
- Databricks MCP governance: <https://learn.microsoft.com/azure/databricks/generative-ai/mcp/#governance>
- Foundry MCP authentication: <https://learn.microsoft.com/azure/foundry/agents/how-to/mcp-authentication>
- Foundry RBAC roles: <https://learn.microsoft.com/azure/ai-services/multi-service-resource#grant-or-obtain-developer-permissions>
- ACR ABAC repository permissions: <https://learn.microsoft.com/azure/container-registry/container-registry-rbac-abac-repository-permissions>

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

Also edit `infra/main.demo.bicepparam` before deployment:

- To reuse an existing Databricks workspace, keep `deployDatabricksWorkspace = false` and replace `existingDatabricksResourceGroupName` / `existingDatabricksWorkspaceName`.
- To create a new workspace, set `deployDatabricksWorkspace = true` and choose the desired Databricks parameters.

## 2. Deploy Azure infrastructure

```bash
./scripts/preflight.sh
./scripts/deploy-infra.sh
```

The Bicep deployment creates:

- Azure Databricks workspace only when `deployDatabricksWorkspace = true`. The demo parameter file is set up to reuse an existing workspace, but you must replace the placeholder `existingDatabricks*` values with your own resource names before deployment.
- ADLS Gen2 storage account for demo/data readiness.
- Microsoft Foundry AI Services account, project, and default `gpt-5.4` model deployment (`gpt-5-4` deployment name, version `2026-03-05`).
- Key Vault with RBAC authorization for future secret references.
- User-assigned managed identity for app/agent runtime use.
- Azure Container Registry for the Foundry Hosted Agent image.
- Optional Azure App Service plan and Linux Web App for the Next.js frontend when `deployFrontendApp = true`.
- Log Analytics workspace and workspace-based Application Insights for agent telemetry, connected to the Foundry account and project so prompt and hosted agent traces can flow to the Foundry Traces experience.

It intentionally does not create Databricks data-plane objects such as SQL Warehouses or Genie Spaces. By default `infra/main.demo.bicepparam` expects an existing Databricks workspace; replace `existingDatabricksResourceGroupName` and `existingDatabricksWorkspaceName` with your values, or set `deployDatabricksWorkspace = true` if you want a fresh workspace. If Foundry model capacity is unavailable in your selected region, set `deployFoundryModel = false` and use an existing model deployment.

After deployment, update `.risk.env.local` with the outputs:

```bash
export DATABRICKS_WORKSPACE_NAME="<databricksWorkspaceName>"
export DATABRICKS_HOST="https://<databricksWorkspaceUrl>"
export FOUNDRY_PROJECT_ENDPOINT="<foundryProjectEndpoint>"
export FOUNDRY_PROJECT_RESOURCE_ID="<foundryProjectResourceId>"
export FOUNDRY_MODEL_DEPLOYMENT="<foundryModelDeploymentName>"
export APPLICATIONINSIGHTS_RESOURCE_ID="<applicationInsightsResourceId>"
export APPLICATIONINSIGHTS_CONNECTION_STRING="<applicationInsightsConnectionString>"
export KEY_VAULT_URI="<keyVaultUri>"
export AZURE_CONTAINER_REGISTRY_NAME="<containerRegistryName>"
export AZURE_CONTAINER_REGISTRY_LOGIN_SERVER="<containerRegistryLoginServer>"
# Present only when deployFrontendApp = true.
export FRONTEND_WEB_APP_NAME="<frontendWebAppName>"
export FRONTEND_WEB_APP_URL="<frontendWebAppUrl>"
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

The default Bicep deployment now creates the Microsoft Foundry AI Services account, Foundry project, and `gpt-5.4` model deployment with deployment name `gpt-5-4` and version `2026-03-05`. Confirm that `.risk.env.local` contains the `foundryProjectEndpoint`, `foundryProjectResourceId`, and `foundryModelDeploymentName` outputs from step 2.

If you disabled `deployFoundryModel` or need a different model for quota/capacity reasons, create or select that deployment in Foundry and set `FOUNDRY_MODEL_DEPLOYMENT` to its deployment name.

The same Bicep deployment also creates `AppInsights` connections at the Foundry account and project scopes. This is required for the prompt Genie agent and the hosted AG-UI agent to show server-side traces in Foundry and to store telemetry in Application Insights. The connection uses the Application Insights connection string as a deployment-time credential; keep `.risk.env.local` private and do not commit it. Microsoft currently documents prompt-agent tracing as generally available and hosted/custom agent tracing as preview.

## 7. Create the Foundry RemoteTool connection and agent

```bash
source .risk.env.local
./scripts/setup-foundry-genie-agent.sh
```

The script:

1. Creates or updates a Foundry `RemoteTool` project connection targeting the Databricks Genie MCP endpoint.
2. Uses `ProjectManagedIdentity` authentication with the Azure Databricks audience.
3. Creates a Foundry prompt agent version with an MCP tool and the instructions from `scripts/foundry-genie-agent-instructions.txt`.
4. Writes `.foundry/agent-metadata.yaml` for the local AG-UI bridge, including the Application Insights resource ID when `APPLICATIONINSIGHTS_RESOURCE_ID` is set.

## 8. Grant Databricks permissions to the Foundry project managed identity

Run this after the SQL Warehouse and Genie Space exist, and before the first agent invocation. It can run before or after creating the Foundry agent because it grants access to the project managed identity, not to an agent version.

```bash
./scripts/grant-databricks-permissions.sh
```

The script grants the Foundry project managed identity:

- Databricks workspace access and Databricks SQL entitlement.
- SQL Warehouse `CAN_USE`.
- Genie Space `CAN_RUN`.
- Unity Catalog `USE_CATALOG`, `USE_SCHEMA`, and `SELECT` on the Risk Exposure view and supporting tables.

## 9. Validate cloud setup without querying data

```bash
./scripts/validate-risk.sh
```

This checks Databricks warehouse metadata, Genie Space metadata, and Foundry connection metadata. It does not invoke Genie.


## 10. Optional: deploy the AG-UI runtime as a Foundry Hosted Agent

Run this only when you want the LangGraph/AG-UI runtime to move from local FastAPI to Microsoft Foundry Agent Service. Complete steps 6-8 first so the hosted runtime can call the Foundry prompt agent and the prompt agent can call Genie.

Build the container image in Azure Container Registry with an immutable timestamp tag. The hosted-agent image must be `linux/amd64`; do not publish or reference `latest`.

```bash
source .risk.env.local
./scripts/build-hosted-agent-image.sh
```

The script uses `apps/agent/Dockerfile` and prints an image reference like:

```text
<acr-login-server>/risk-exposure-ag-ui-hosted:20260519123045
```

Create or update the Foundry Hosted Agent from `apps/agent/agent.yaml` and set the container image to that exact reference. Keep the manifest environment values deterministic using the `RISK_GENIE_*` names from the manifest; Foundry reserves `FOUNDRY_*` and `AGENT_*` for platform use in hosted containers. Do not place secrets in the image or manifest; use managed identity and Key Vault-backed configuration for production hardening.

Before the first invocation, verify these access assignments:

- The Foundry project managed identity has ACR `Container Registry Repository Reader` on the registry. The Bicep deployment assigns this for the project identity.
- If the Hosted Agent service creates a per-agent managed identity, assign it the same ACR reader role if image pull fails.
- The identity used by the web/API caller has `Foundry User` / `Azure AI User`-equivalent invoke permission at the Foundry account or project scope.
- If Foundry reports an invocation identity during hosted-agent creation, assign that identity the required Foundry invoke role at the Foundry account scope.

Then configure the Next.js BFF to call the hosted Invocations endpoint instead of local FastAPI:

```bash
export AG_UI_AGENT_URL="https://<hosted-agent-invocations-endpoint>"
export AG_UI_AGENT_AUTH="azure-identity"
# Optional; this is the default scope used by the route.
export AG_UI_AGENT_SCOPE="https://ai.azure.com/.default"
```

Validate with a safe prompt first, then run a governed Genie query. After validation, check Foundry Traces or Application Insights for both `risk-exposure-genie-agent` and `risk-exposure-ag-ui-hosted`. Useful workspace-based Application Insights tables are `AppRequests`, `AppDependencies`, `AppTraces`, and `AppGenAIContent`. Keep Databricks compute stopped when the demo is idle.

## 11. Optional: deploy the Next.js frontend to Azure App Service

Use this only when you want the browser-facing Next.js app hosted in Azure instead of on your laptop. This adds an App Service plan and Linux Web App, so expect ongoing App Service cost until you delete or scale down the resource.

Complete step 10 first and copy the Foundry Hosted Agent Invocations endpoint. Then edit `infra/main.demo.bicepparam`:

```bicep
param deployFrontendApp = true
param frontendAgUiAgentUrl = 'https://<hosted-agent-invocations-endpoint>'
// Optional cost/performance override; keep tier aligned with the SKU.
param frontendAppServicePlanSkuName = 'B1'
param frontendAppServicePlanSkuTier = 'Basic'
```

Deploy the infrastructure change. `deploy-infra.sh` runs `what-if` first and asks for confirmation before applying changes:

```bash
source .risk.env.local
./scripts/deploy-infra.sh
```

Copy the new outputs into `.risk.env.local`:

```bash
export FRONTEND_WEB_APP_NAME="<frontendWebAppName>"
export FRONTEND_WEB_APP_URL="<frontendWebAppUrl>"
```

Build and publish a precompiled standalone Next.js package. This keeps App Service from running a remote Oryx build during deployment:

```bash
npm run build:web
rm -rf /tmp/risk-frontend-standalone /tmp/risk-frontend.zip
mkdir -p /tmp/risk-frontend-standalone/apps/web/.next
cp -R apps/web/.next/standalone/. /tmp/risk-frontend-standalone/
cp -R apps/web/.next/static /tmp/risk-frontend-standalone/apps/web/.next/static
if [ -d apps/web/public ]; then
  cp -R apps/web/public /tmp/risk-frontend-standalone/apps/web/public
fi
(
  cd /tmp/risk-frontend-standalone
  zip -qr /tmp/risk-frontend.zip .
)
az webapp deploy \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FRONTEND_WEB_APP_NAME" \
  --src-path /tmp/risk-frontend.zip \
  --type zip
```

Open `$FRONTEND_WEB_APP_URL` and validate with a safe prompt before any governed Genie query. The web app uses its system-assigned managed identity to request `https://ai.azure.com/.default` tokens; the Bicep role assignment grants that identity Foundry invoke access at the Foundry account scope when `deployFrontendApp = true`.

## 12. Stop compute after setup or demo

```bash
./scripts/stop-compute.sh
./scripts/validate-risk.sh
```
