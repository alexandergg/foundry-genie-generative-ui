# Cost control

The main variable cost for this demo is Databricks compute, especially the SQL Warehouse used by Genie.

## Operating rules

- Keep the SQL Warehouse stopped except during setup and live demos.
- Use Serverless SQL `2X-Small` if available; otherwise use Pro `2X-Small`.
- Configure aggressive auto-stop: 5 minutes for Serverless when possible, 10 minutes for Pro.
- Do not leave interactive/all-purpose clusters running.
- Delete the resource group if the demo will not continue.

## Stop and validate

```bash
source .risk.env.local
./scripts/stop-compute.sh
./scripts/validate-risk.sh
```

Desired state:

- Risk Exposure SQL Warehouse: `STOPPED`.
- Interactive/all-purpose clusters: `0` running.
- Instance pools: `0` unless deliberately configured.

With the warehouse stopped, Databricks SQL DBU cost should be near zero. Residual cost can remain for network, storage, logs, and managed workspace resources. For minimum cost, delete the resource group:

```bash
./scripts/delete-resources.sh
```
