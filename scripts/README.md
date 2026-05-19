# Scripts

Scripts are named descriptively; run them in the setup order documented below instead of relying on numeric filename prefixes.

## Recommended setup order

1. `preflight.sh` — check Azure account, provider registration, regional availability, and quota signals.
2. `deploy-infra.sh` — create/update the Azure app/agent resource group after `what-if` review; by default it reuses the existing Databricks workspace configured in `infra/main.demo.bicepparam` and connects Foundry to workspace-based Application Insights for traces.
3. `create-warehouse.sh` — create or discover the Databricks SQL Warehouse.
4. `run-demo-sql.sh` — load the synthetic Risk Exposure demo data and view.
5. `create-genie-space.sh` — create or discover the Databricks Genie Space.
6. `setup-foundry-genie-agent.sh` — create the Foundry RemoteTool connection and Prompt Agent version using `foundry-genie-agent-instructions.txt`.
7. `grant-databricks-permissions.sh` — grant the Foundry managed identity Databricks access.
8. `validate-risk.sh` — validate resources without invoking Genie.
9. `build-hosted-agent-image.sh` — optional, opt-in ACR cloud build for the Foundry Hosted Agent image.
10. `stop-compute.sh` — stop the SQL Warehouse to minimize cost.

See `docs/azure-setup.md` for the full walkthrough.
