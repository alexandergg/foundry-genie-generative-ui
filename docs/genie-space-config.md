# Genie Space configuration

Use this after Azure infrastructure is deployed and Unity Catalog is available.

## Recommended warehouse

- Type: Serverless SQL if enabled; otherwise Pro SQL.
- Size: `2X-Small`.
- Min/max clusters: `1 / 1`.
- Auto-stop: `5-10` minutes.
- Start it only for setup or live demos.

## Genie Space scope

Create one Genie Space for the curated Risk Exposure data scope:

- Preferred object: `${DEMO_CATALOG}.${DEMO_SCHEMA}.vw_risk_genie_exposure_claims`
- Optional supporting objects:
  - `fact_exposure`
  - `fact_claim`
  - `dim_broker`

Suggested description:

> Conversational analytics over synthetic exposure, overdue balance, claims and broker segment data. Use this space to answer business questions about exposure, risk class, country, product line, legal entity, broker segment, broker name and fiscal quarter.

## Instructions for Genie

Add guidance similar to:

```text
Use vw_risk_genie_exposure_claims as the preferred business-facing object.
Treat total_exposure_eur, total_overdue_balance_eur and total_claim_amount_eur as EUR amounts.
Use fiscal_quarter for quarter comparisons.
Use risk_class A/B/C where A is lower risk and C is higher risk for this synthetic demo.
When possible, return grouped results as tables with stable column names and numeric values.
Do not infer PII; this demo dataset is synthetic and aggregated.
```

## Readiness checks

- Unity Catalog is enabled and attached to the workspace.
- Partner-powered AI / Genie features are enabled according to workspace policy.
- The setup user has Databricks SQL entitlement, `CAN USE` on the warehouse, and `SELECT` on the UC objects.
- Demo users have `CAN VIEW` / `CAN RUN` on the Genie Space and `SELECT` on the data.
- The Foundry project managed identity has `CAN_RUN` on Genie, `CAN_USE` on the warehouse, Databricks SQL entitlement, and `SELECT` on the Risk Exposure view/supporting tables.
