#!/usr/bin/env python3
"""Deterministically generate the enriched Risk Exposure demo SQL.

Writes databricks/sql/risk_demo_setup.sql with:
  - dim_broker (curated, unchanged contract)
  - fact_exposure (8 quarters 2025-Q1..2026-Q4, ~110 policies, mild upward trend)
  - fact_claim (claims spread across months/statuses)
  - vw_uc3_genie_exposure_claims (UNCHANGED column contract — consumed by Genie)

The objects use CREATE ... IF NOT EXISTS + INSERT OVERWRITE rather than
CREATE OR REPLACE, so a data refresh replaces rows WITHOUT recreating the objects
— recreating would reset Unity Catalog grants and break the Foundry/Genie identity's
SELECT access. Trade-off: if a column or the view definition changes, DROP the
object manually first so the new definition takes effect.

Deterministic: no randomness, output is stable across runs. Re-run after editing
this generator, then upload with scripts/run-demo-sql.sh.
"""
from __future__ import annotations

from pathlib import Path

# (broker_id, name, segment, country)
BROKERS = [
    ("B001", "North Trade Brokers", "Enterprise", "Netherlands"),
    ("B002", "Iberia Credit Partners", "SME", "Spain"),
    ("B003", "DACH Risk Advisors", "Mid-Market", "Germany"),
    ("B004", "Benelux Coverage Group", "Enterprise", "Belgium"),
    ("B005", "France Trade Assurance", "SME", "France"),
    ("B006", "Nordic Credit Shield", "Enterprise", "Sweden"),
    ("B007", "Italia Trade Risk", "Mid-Market", "Italy"),
    ("B008", "UK Working Capital Partners", "Enterprise", "United Kingdom"),
    ("B009", "Poland Receivables Hub", "SME", "Poland"),
    ("B010", "Portugal Export Cover", "SME", "Portugal"),
]

COUNTRY_CODE = {
    "Netherlands": "NL", "Spain": "ES", "Germany": "DE", "Belgium": "BE",
    "France": "FR", "Sweden": "SE", "Italy": "IT", "United Kingdom": "UK",
    "Poland": "PL", "Portugal": "PT",
}

QUARTERS = [f"{y}-Q{q}" for y in (2025, 2026) for q in (1, 2, 3, 4)]  # 8 quarters
QUARTER_MONTHS = {  # fiscal quarter -> representative months for claims
    1: ("01", "02", "03"), 2: ("04", "05", "06"),
    3: ("07", "08", "09"), 4: ("10", "11", "12"),
}
PRODUCT_LINES = ["Trade Credit", "Surety", "Collections", "Bonding"]
RISK_CLASSES = ["A", "B", "C"]
# base exposure (EUR) by segment
SEGMENT_BASE = {"Enterprise": 1_600_000, "Mid-Market": 950_000, "SME": 620_000}
# overdue rate by risk class
OVERDUE_RATE = {"A": 0.015, "B": 0.045, "C": 0.11}
CLAIM_STATUSES = ["Open", "In Review", "Closed"]


def policies_per_quarter(segment: str) -> int:
    return 2 if segment == "Enterprise" else 1


def round_k(x: float) -> int:
    """Round to the nearest 1,000 for tidy demo figures."""
    return int(round(x / 1000.0)) * 1000


def gen_exposure() -> list[tuple]:
    rows: list[tuple] = []
    pid = 10001
    for bi, (broker_id, _name, segment, country) in enumerate(BROKERS):
        code = COUNTRY_CODE[country]
        legal_entity = f"Contoso {code}"
        base = SEGMENT_BASE[segment]
        for qi, quarter in enumerate(QUARTERS):
            for slot in range(policies_per_quarter(segment)):
                product = PRODUCT_LINES[(bi + qi + slot) % len(PRODUCT_LINES)]
                # deterministic risk: each broker leans to a tier, drifts a little
                risk = RISK_CLASSES[(bi * 2 + qi + slot) % 3]
                growth = 1.0 + 0.025 * qi          # mild upward trend over quarters
                wobble = 0.85 + ((bi * 7 + qi * 3 + slot * 5) % 9) / 30.0  # 0.85..1.12
                product_factor = 1.0 + 0.12 * (PRODUCT_LINES.index(product) - 1)
                exposure = round_k(base * growth * wobble * product_factor)
                overdue = round_k(exposure * OVERDUE_RATE[risk]
                                  * (0.7 + ((bi + qi + slot) % 5) / 6.0))
                rows.append((f"P{pid}", broker_id, legal_entity, country, risk,
                             product, quarter, exposure, overdue))
                pid += 1
    return rows


def gen_claims(exposure_rows: list[tuple]) -> list[tuple]:
    rows: list[tuple] = []
    cid = 9001
    for idx, e in enumerate(exposure_rows):
        policy_id, _b, _le, _c, risk, _p, quarter, exposure, overdue = e
        # claims concentrate on riskier policies; ~1 in 3 of B/C generate a claim
        if risk == "A" or idx % 3 != 0:
            continue
        q_num = int(quarter.split("-Q")[1])
        year = quarter.split("-Q")[0]
        month = QUARTER_MONTHS[q_num][idx % 3]
        status = CLAIM_STATUSES[idx % len(CLAIM_STATUSES)]
        amount = round_k(max(overdue, exposure * 0.05) * (0.6 + (idx % 4) / 5.0))
        rows.append((f"C{cid}", policy_id, status, amount, f"{year}-{month}"))
        cid += 1
    return rows


def sql_str(v: str) -> str:
    return "'" + v.replace("'", "''") + "'"


def values_block(rows: list[tuple]) -> str:
    out = []
    for r in rows:
        cells = []
        for v in r:
            cells.append(sql_str(v) if isinstance(v, str) else f"{v:.2f}")
        out.append("  (" + ", ".join(cells) + ")")
    return ",\n".join(out) + ";"


def main() -> None:
    exposure = gen_exposure()
    claims = gen_claims(exposure)

    broker_values = ",\n".join(
        f"  ({sql_str(b)}, {sql_str(n)}, {sql_str(s)}, {sql_str(c)})"
        for b, n, s, c in BROKERS
    ) + ";"

    sql = f"""-- Risk Exposure Databricks Genie demo data setup.
-- GENERATED by scripts/gen-risk-demo-sql.py — do not edit by hand; edit the generator.
-- The catalog/schema already exist in the deployed workspace (Default Storage
-- metastore cannot CREATE CATALOG without a managed location), so we only USE them.
-- Objects use CREATE ... IF NOT EXISTS + INSERT OVERWRITE so a data refresh keeps
-- existing Unity Catalog grants intact. scripts/run-demo-sql.sh rewrites
-- 'risk_demo' -> $DEMO_CATALOG and 'analytics' -> $DEMO_SCHEMA before running.

USE CATALOG risk_demo;
USE SCHEMA analytics;

CREATE TABLE IF NOT EXISTS dim_broker (
  broker_id STRING COMMENT 'Unique broker identifier',
  broker_name STRING COMMENT 'Broker display name',
  broker_segment STRING COMMENT 'Commercial segment of the broker',
  broker_country STRING COMMENT 'Primary broker country'
)
USING DELTA
COMMENT 'Curated broker dimension for Risk Exposure Genie demo';

INSERT OVERWRITE dim_broker VALUES
{broker_values}

CREATE TABLE IF NOT EXISTS fact_exposure (
  policy_id STRING COMMENT 'Policy identifier',
  broker_id STRING COMMENT 'Broker identifier linked to dim_broker',
  legal_entity STRING COMMENT 'Synthetic legal entity',
  country STRING COMMENT 'Exposure country',
  risk_class STRING COMMENT 'Risk class assigned by underwriting',
  product_line STRING COMMENT 'Insurance product line',
  fiscal_quarter STRING COMMENT 'Fiscal quarter in YYYY-Qn format',
  exposure_eur DECIMAL(18,2) COMMENT 'Total credit exposure in EUR',
  overdue_balance_eur DECIMAL(18,2) COMMENT 'Overdue outstanding balance in EUR'
)
USING DELTA
COMMENT 'Curated exposure fact table for Risk Exposure Genie demo';

INSERT OVERWRITE fact_exposure VALUES
{values_block(exposure)}

CREATE TABLE IF NOT EXISTS fact_claim (
  claim_id STRING COMMENT 'Claim identifier',
  policy_id STRING COMMENT 'Policy identifier linked to fact_exposure',
  claim_status STRING COMMENT 'Lifecycle status of the claim',
  claim_amount_eur DECIMAL(18,2) COMMENT 'Claim amount in EUR',
  claim_month STRING COMMENT 'Claim month in YYYY-MM format'
)
USING DELTA
COMMENT 'Curated claims fact table for Risk Exposure Genie demo';

INSERT OVERWRITE fact_claim VALUES
{values_block(claims)}

-- View name matches the deployed Genie Space object (vw_uc3_genie_exposure_claims).
-- Views are not materialized, so refreshing the tables above already updates it;
-- IF NOT EXISTS avoids recreating it (which would drop its SELECT grant for Genie).
CREATE VIEW IF NOT EXISTS vw_uc3_genie_exposure_claims
COMMENT 'Genie-ready curated view joining exposure, broker and claim signals for business questions'
AS
SELECT
  e.fiscal_quarter,
  e.country,
  e.legal_entity,
  e.risk_class,
  e.product_line,
  b.broker_segment,
  b.broker_name,
  COUNT(DISTINCT e.policy_id) AS policy_count,
  SUM(e.exposure_eur) AS total_exposure_eur,
  SUM(e.overdue_balance_eur) AS total_overdue_balance_eur,
  SUM(COALESCE(c.claim_amount_eur, 0)) AS total_claim_amount_eur,
  COUNT(DISTINCT c.claim_id) AS claim_count
FROM fact_exposure e
JOIN dim_broker b ON e.broker_id = b.broker_id
LEFT JOIN fact_claim c ON e.policy_id = c.policy_id
GROUP BY ALL;

-- Useful checks for the demo:
SELECT * FROM vw_uc3_genie_exposure_claims ORDER BY fiscal_quarter, country;
"""

    out_path = Path(__file__).resolve().parents[1] / "databricks" / "sql" / "risk_demo_setup.sql"
    out_path.write_text(sql, encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"  brokers : {len(BROKERS)}")
    print(f"  exposure: {len(exposure)} rows across {len(QUARTERS)} quarters")
    print(f"  claims  : {len(claims)} rows")


if __name__ == "__main__":
    main()
