-- UC3 Databricks Genie demo data setup.
-- Run in Databricks SQL after selecting a Pro or Serverless SQL warehouse.
-- Adjust catalog/schema names if your workspace policy requires a different catalog.

CREATE CATALOG IF NOT EXISTS uc3_risk_demo COMMENT 'UC3 catalog for the Risk & Exposure Genie demo';
CREATE SCHEMA IF NOT EXISTS uc3_risk_demo.analytics COMMENT 'Curated analytical schema for the Genie UC3 demo';

USE CATALOG uc3_risk_demo;
USE SCHEMA analytics;

CREATE OR REPLACE TABLE dim_broker (
  broker_id STRING COMMENT 'Unique broker identifier',
  broker_name STRING COMMENT 'Broker display name',
  broker_segment STRING COMMENT 'Commercial segment of the broker',
  broker_country STRING COMMENT 'Primary broker country'
)
USING DELTA
COMMENT 'Curated broker dimension for UC3 Genie demo';

INSERT OVERWRITE dim_broker VALUES
  ('B001', 'North Trade Brokers', 'Enterprise', 'Netherlands'),
  ('B002', 'Iberia Credit Partners', 'SME', 'Spain'),
  ('B003', 'DACH Risk Advisors', 'Mid-Market', 'Germany'),
  ('B004', 'Benelux Coverage Group', 'Enterprise', 'Belgium'),
  ('B005', 'France Trade Assurance', 'SME', 'France'),
  ('B006', 'Nordic Credit Shield', 'Enterprise', 'Sweden'),
  ('B007', 'Italia Trade Risk', 'Mid-Market', 'Italy'),
  ('B008', 'UK Working Capital Partners', 'Enterprise', 'United Kingdom'),
  ('B009', 'Poland Receivables Hub', 'SME', 'Poland'),
  ('B010', 'Portugal Export Cover', 'SME', 'Portugal');

CREATE OR REPLACE TABLE fact_exposure (
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
COMMENT 'Curated exposure fact table for UC3 Genie demo';

INSERT OVERWRITE fact_exposure VALUES
  ('P1001', 'B001', 'Contoso NL', 'Netherlands', 'A', 'Trade Credit', '2026-Q1', 1250000.00, 25000.00),
  ('P1002', 'B002', 'Contoso ES', 'Spain', 'B', 'Trade Credit', '2026-Q1', 780000.00, 42000.00),
  ('P1003', 'B003', 'Contoso DE', 'Germany', 'A', 'Surety', '2026-Q1', 2100000.00, 18000.00),
  ('P1004', 'B004', 'Contoso BE', 'Belgium', 'C', 'Trade Credit', '2026-Q1', 640000.00, 96000.00),
  ('P1005', 'B005', 'Contoso FR', 'France', 'B', 'Collections', '2026-Q1', 520000.00, 51000.00),
  ('P1011', 'B006', 'Contoso SE', 'Sweden', 'A', 'Trade Credit', '2026-Q1', 760000.00, 12000.00),
  ('P1012', 'B007', 'Contoso IT', 'Italy', 'C', 'Trade Credit', '2026-Q1', 840000.00, 118000.00),
  ('P1013', 'B008', 'Contoso UK', 'United Kingdom', 'B', 'Bonding', '2026-Q1', 1350000.00, 33000.00),
  ('P1006', 'B002', 'Contoso ES', 'Spain', 'A', 'Trade Credit', '2026-Q2', 930000.00, 19000.00),
  ('P1007', 'B001', 'Contoso NL', 'Netherlands', 'B', 'Surety', '2026-Q2', 1540000.00, 31000.00),
  ('P1008', 'B003', 'Contoso DE', 'Germany', 'C', 'Trade Credit', '2026-Q2', 870000.00, 123000.00),
  ('P1009', 'B004', 'Contoso BE', 'Belgium', 'A', 'Collections', '2026-Q2', 410000.00, 15000.00),
  ('P1010', 'B005', 'Contoso FR', 'France', 'B', 'Trade Credit', '2026-Q2', 690000.00, 44000.00),
  ('P1014', 'B008', 'Contoso UK', 'United Kingdom', 'A', 'Trade Credit', '2026-Q2', 1680000.00, 27000.00),
  ('P1015', 'B009', 'Contoso PL', 'Poland', 'C', 'Trade Credit', '2026-Q2', 590000.00, 88000.00),
  ('P1016', 'B010', 'Contoso PT', 'Portugal', 'B', 'Collections', '2026-Q2', 360000.00, 37000.00),
  ('P1017', 'B006', 'Contoso SE', 'Sweden', 'A', 'Surety', '2026-Q3', 980000.00, 16000.00),
  ('P1018', 'B007', 'Contoso IT', 'Italy', 'C', 'Trade Credit', '2026-Q3', 910000.00, 141000.00),
  ('P1019', 'B008', 'Contoso UK', 'United Kingdom', 'B', 'Trade Credit', '2026-Q3', 1720000.00, 49000.00),
  ('P1020', 'B003', 'Contoso DE', 'Germany', 'A', 'Bonding', '2026-Q3', 1180000.00, 22000.00);

CREATE OR REPLACE TABLE fact_claim (
  claim_id STRING COMMENT 'Claim identifier',
  policy_id STRING COMMENT 'Policy identifier linked to fact_exposure',
  claim_status STRING COMMENT 'Lifecycle status of the claim',
  claim_amount_eur DECIMAL(18,2) COMMENT 'Claim amount in EUR',
  claim_month STRING COMMENT 'Claim month in YYYY-MM format'
)
USING DELTA
COMMENT 'Curated claims fact table for UC3 Genie demo';

INSERT OVERWRITE fact_claim VALUES
  ('C9001', 'P1002', 'Open', 18000.00, '2026-01'),
  ('C9002', 'P1004', 'Open', 45000.00, '2026-02'),
  ('C9003', 'P1005', 'Closed', 22000.00, '2026-02'),
  ('C9004', 'P1008', 'Open', 64000.00, '2026-04'),
  ('C9005', 'P1010', 'In Review', 28000.00, '2026-05'),
  ('C9006', 'P1012', 'Open', 73000.00, '2026-03'),
  ('C9007', 'P1014', 'Closed', 36000.00, '2026-04'),
  ('C9008', 'P1015', 'Open', 52000.00, '2026-05'),
  ('C9009', 'P1018', 'In Review', 81000.00, '2026-07'),
  ('C9010', 'P1019', 'Open', 41000.00, '2026-08'),
  ('C9011', 'P1020', 'Closed', 19000.00, '2026-09');

CREATE OR REPLACE VIEW vw_uc3_genie_exposure_claims
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
