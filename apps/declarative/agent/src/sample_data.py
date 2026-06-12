"""Inline sample dataset for the declarative A2UI report demo.

The whole point of this demo is the *composition contract* (a component
catalog + schemas + data), so the data is a small static energy-portfolio risk
table — no Databricks, no Genie, no network. `build_report_view` is pure: the
same quarter always produces the same view, which keeps the fixed-schema demo
deterministic on stage.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Literal

LayoutId = Literal["executive", "brief"]

QUARTERS: tuple[str, ...] = ("2026-Q1", "2026-Q2")
DEFAULT_QUARTER = "2026-Q2"

TOP_EXPOSURES_LIMIT = 5


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


@dataclass(frozen=True)
class ReportView:
    """Everything the fixed layouts need: path-bound data model + inline component data."""

    quarter: str
    data_model: dict[str, Any]
    kpis: list[dict[str, str]]
    bar_data: list[dict[str, Any]]
    pie_data: list[dict[str, Any]]
    table_columns: list[dict[str, str]]
    table_rows: list[dict[str, str]]


def _rows_for(quarter: str) -> list[RiskRow]:
    return [row for row in RISK_ROWS if row.quarter == quarter]


def _fmt_meur(value: float) -> str:
    return f"€{value:,.1f}M"


def _fmt_pct(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.1f}%"


def _previous_quarter(quarter: str) -> str | None:
    index = QUARTERS.index(quarter) if quarter in QUARTERS else -1
    return QUARTERS[index - 1] if index > 0 else None


def _totals(rows: list[RiskRow]) -> dict[str, float]:
    return {
        "exposure": sum(row.exposure_meur for row in rows),
        "claims": sum(row.claims_meur for row in rows),
        "overdue": sum(row.overdue_meur for row in rows),
    }


def _exposure_by_country(rows: list[RiskRow]) -> list[tuple[str, float]]:
    by_country: dict[str, float] = {}
    for row in rows:
        by_country[row.country] = by_country.get(row.country, 0.0) + row.exposure_meur
    return sorted(by_country.items(), key=lambda item: item[1], reverse=True)


def quarter_aggregates() -> dict[str, dict[str, str]]:
    """Compact per-quarter totals for the planner LLM prompt (so the summary never invents numbers)."""
    return {quarter: {key: _fmt_meur(value) for key, value in _totals(_rows_for(quarter)).items()} for quarter in QUARTERS}


def dataset_json() -> str:
    """Full dataset as JSON, used to ground the dynamic-schema prompt."""
    return json.dumps([asdict(row) for row in RISK_ROWS], ensure_ascii=False)


def build_report_view(quarter: str, layout_id: LayoutId = "executive") -> ReportView:
    """Build the deterministic view model the fixed A2UI layouts are filled with."""
    if quarter not in QUARTERS:
        quarter = DEFAULT_QUARTER
    rows = _rows_for(quarter)
    totals = _totals(rows)
    previous_quarter = _previous_quarter(quarter)
    previous_totals = _totals(_rows_for(previous_quarter)) if previous_quarter else None

    def kpi(label: str, key: str) -> dict[str, str]:
        if previous_totals is None or previous_totals[key] == 0:
            return {"label": label, "value": _fmt_meur(totals[key]), "trend": "neutral", "trendValue": "baseline quarter"}
        change = (totals[key] - previous_totals[key]) / previous_totals[key] * 100
        trend = "up" if change >= 0.05 else ("down" if change <= -0.05 else "neutral")
        return {
            "label": label,
            "value": _fmt_meur(totals[key]),
            "trend": trend,
            "trendValue": f"{_fmt_pct(change)} vs {previous_quarter}",
        }

    top_rows = sorted(rows, key=lambda row: row.exposure_meur, reverse=True)[:TOP_EXPOSURES_LIMIT]
    country_exposure = _exposure_by_country(rows)

    def country_row(country: str) -> dict[str, str]:
        subset = [row for row in rows if row.country == country]
        sub_totals = _totals(subset)
        return {
            "country": country,
            "exposure": _fmt_meur(sub_totals["exposure"]),
            "claims": _fmt_meur(sub_totals["claims"]),
            "overdue": _fmt_meur(sub_totals["overdue"]),
        }

    title = f"Executive risk report — {quarter}" if layout_id == "executive" else f"Risk brief — {quarter}"
    return ReportView(
        quarter=quarter,
        data_model={
            "report": {
                "title": title,
                "subtitle": "Energy portfolio · inline governed sample · declarative A2UI",
                "topExposures": [{"name": f"{row.country} · {row.sector}", "amount": _fmt_meur(row.exposure_meur)} for row in top_rows],
                "footnote": "Source: inline sample dataset (no external systems). Catalog: copilotkit://risk-catalog.",
            }
        },
        kpis=[
            kpi("Total exposure", "exposure"),
            kpi("Total claims", "claims"),
            kpi("Overdue balance", "overdue"),
        ],
        bar_data=[{"label": country, "value": round(value, 1)} for country, value in country_exposure],
        pie_data=[{"label": country, "value": round(value, 1)} for country, value in country_exposure],
        table_columns=[
            {"key": "country", "label": "Country"},
            {"key": "exposure", "label": "Exposure"},
            {"key": "claims", "label": "Claims"},
            {"key": "overdue", "label": "Overdue"},
        ],
        table_rows=[country_row(country) for country, _ in country_exposure],
    )
