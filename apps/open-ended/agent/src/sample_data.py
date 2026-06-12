"""Inline sample dataset for the open-ended A2UI demo.

Same energy-portfolio risk numbers as the declarative demo, but here they are
only *prompt grounding*: the LLM invents the component tree itself, and the
preamble pins every figure it is allowed to show.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RiskRow:
    country: str
    sector: str
    quarter: str
    exposure_meur: float
    claims_meur: float
    overdue_meur: float


RISK_ROWS: tuple[RiskRow, ...] = (
    RiskRow("Spain", "Solar PV", "2026-Q1", 281.0, 17.2, 12.4),
    RiskRow("Spain", "Wind Onshore", "2026-Q1", 199.5, 11.8, 8.9),
    RiskRow("Mexico", "Wind Onshore", "2026-Q1", 152.0, 14.6, 11.2),
    RiskRow("Chile", "Solar PV", "2026-Q1", 121.4, 6.1, 4.3),
    RiskRow("Australia", "Storage", "2026-Q1", 96.7, 3.9, 2.1),
    RiskRow("Poland", "Transmission", "2026-Q1", 78.2, 5.4, 6.0),
    RiskRow("Spain", "Solar PV", "2026-Q2", 312.5, 19.8, 10.6),
    RiskRow("Spain", "Wind Onshore", "2026-Q2", 204.9, 10.2, 7.4),
    RiskRow("Mexico", "Wind Onshore", "2026-Q2", 148.3, 18.9, 16.8),
    RiskRow("Chile", "Solar PV", "2026-Q2", 133.0, 5.7, 3.9),
    RiskRow("Australia", "Storage", "2026-Q2", 109.8, 4.2, 1.8),
    RiskRow("Poland", "Transmission", "2026-Q2", 71.6, 7.9, 9.3),
)


def domain_preamble() -> str:
    rows = json.dumps([asdict(row) for row in RISK_ROWS], ensure_ascii=False)
    return (
        "## DOMAIN\n"
        "You are inventing a UI for this energy-portfolio risk dataset (amounts in million EUR). "
        "Choose ANY layout you want — dashboards, briefings, comparisons, forms — but ground every number "
        "you display in this data and never invent figures. Reply in the user's language.\n"
        f"Dataset rows: {rows}"
    )
