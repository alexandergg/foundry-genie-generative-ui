from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .component_registry import validate_component_name
from .normalization import NormalizationWarning, build_visual_meta


@dataclass
class ComponentCall:
    name: str
    args: dict[str, Any]

    def __post_init__(self) -> None:
        self.name = validate_component_name(self.name)


def _parse_number(value: str) -> float | None:
    if re.search(r"[A-Za-z]", value):
        return None
    cleaned = re.sub(r"[^0-9,.-]", "", value).strip()
    if not cleaned:
        return None

    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".") if cleaned.rfind(",") > cleaned.rfind(".") else cleaned.replace(",", "")
    elif cleaned.count(".") > 1:
        cleaned = cleaned.replace(".", "")
    elif cleaned.count(",") > 1:
        cleaned = cleaned.replace(",", "")
    elif cleaned.count(".") == 1 and len(cleaned.rsplit(".", 1)[1]) == 3:
        cleaned = cleaned.replace(".", "")
    elif cleaned.count(",") == 1 and cleaned.count(".") == 0:
        integer, decimal = cleaned.rsplit(",", 1)
        cleaned = integer + decimal if len(decimal) == 3 else f"{integer}.{decimal}"

    try:
        return float(cleaned)
    except ValueError:
        return None


def _humanize(key: str) -> str:
    return key.replace("_", " ").strip().title()


def extract_markdown_table(text: str) -> tuple[list[str], list[dict[str, Any]]]:
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|") and line.strip().endswith("|")]
    if len(lines) < 3:
        return [], []

    header = [cell.strip() for cell in lines[0].strip("|").split("|")]
    separator = [cell.strip() for cell in lines[1].strip("|").split("|")]
    if not all(set(cell) <= {"-", ":", " "} for cell in separator):
        return [], []

    rows: list[dict[str, Any]] = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(header):
            continue
        row: dict[str, Any] = {}
        for key, raw in zip(header, cells, strict=True):
            number = _parse_number(raw)
            row[key] = number if number is not None else raw
        rows.append(row)
    return header, rows


def _metric_key_for_question(question: str) -> str:
    lowered = question.lower()
    if "claim" in lowered or "siniestro" in lowered:
        return "total_claim_amount_eur"
    if "overdue" in lowered or "vencido" in lowered:
        return "total_overdue_balance_eur"
    if "polic" in lowered:
        return "policy_count"
    return "total_exposure_eur"


def extract_bullet_metrics(text: str, question: str) -> tuple[list[str], list[dict[str, Any]]]:
    metric_key = _metric_key_for_question(question)
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        match = re.match(r"^\s*[-*]\s*(?P<label>[^:]+):\s*(?P<value>.+?)\s*$", line)
        if not match:
            continue
        number = _parse_number(match.group("value"))
        if number is not None:
            rows.append({"label": match.group("label").strip(), metric_key: number})
    return (["label", metric_key], rows) if rows else ([], [])


def _pick_keys(headers: list[str], rows: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    if not rows:
        return None, None
    label_key = next((h for h in headers if not isinstance(rows[0].get(h), (int, float))), None)
    preferred = ["total_exposure_eur", "total_claim_amount_eur", "total_overdue_balance_eur", "claim_count", "policy_count"]
    lower_to_original = {h.lower(): h for h in headers}
    value_key = next((lower_to_original[k] for k in preferred if k in lower_to_original), None)
    if not value_key:
        value_key = next((h for h in headers if isinstance(rows[0].get(h), (int, float))), None)
    return label_key, value_key


def _numeric_keys(headers: list[str], rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    return [h for h in headers if isinstance(rows[0].get(h), (int, float))]


def _is_time_like_key(key: str, rows: list[dict[str, Any]]) -> bool:
    key_l = key.lower()
    if any(token in key_l for token in ["quarter", "period", "month", "date", "year"]):
        return True
    values = [str(row.get(key, "")) for row in rows[:6]]
    return any(re.search(r"20\d{2}[-_ ]?q[1-4]|q[1-4][-_ ]?20\d{2}", value.lower()) for value in values)


def _format_for_key(key: str) -> str:
    return "currency" if "eur" in key.lower() or "amount" in key.lower() or "balance" in key.lower() else "number"


def _status_for_metric(key: str) -> str:
    lowered = key.lower()
    if "overdue" in lowered or "breach" in lowered:
        return "critical"
    if "claim" in lowered or "loss" in lowered or "balance" in lowered:
        return "attention"
    return "stable"


def build_follow_up_questions(question: str) -> list[str]:
    lowered = question.lower()
    if "2026-q1" in lowered and "2026-q2" in lowered:
        return [
            "Which countries explain the exposure variation between 2026-Q1 and 2026-Q2?",
            "Break down overdue balance by risk class for 2026-Q2.",
            "Compare exposure and claims by broker between 2026-Q1 and 2026-Q2.",
        ]
    if "broker" in lowered or "claim" in lowered or "siniestro" in lowered:
        return [
            "Give me the top 5 brokers by overdue balance in 2026-Q2.",
            "Cross claim amount with exposure by broker_segment.",
            "Which open claims require priority attention?",
        ]
    if "risk" in lowered or "riesgo" in lowered or "vencido" in lowered or "overdue" in lowered:
        return [
            "Show overdue balance by country and risk class.",
            "Which risk class has the highest overdue balance / exposure ratio?",
            "Compare risk classes A, B and C between 2026-Q1 and 2026-Q2.",
        ]
    return [
        "Drill down by country and product_line for 2026-Q2.",
        "Compare exposure, overdue balance and claims by broker_segment.",
        "Where should the executive risk review focus?",
    ]


def build_component_calls(
    question: str,
    answer: str,
    warehouse_name: str | None = None,
    approval_request_id: str | None = None,
    trace_id: str | None = None,
) -> list[ComponentCall]:
    headers, rows = extract_markdown_table(answer)
    if not rows:
        headers, rows = extract_bullet_metrics(answer, question)
    label_key, value_key = _pick_keys(headers, rows)
    source = warehouse_name or "Azure AI Foundry + Databricks Genie"
    generated_at = datetime.now(timezone.utc)
    visual_index = 0
    warnings = [] if rows else [NormalizationWarning("no_structured_rows", "No structured rows were detected; narrative only.")]

    def with_provenance(
        component_name: str, args: dict[str, Any], row_count: int, component_warnings: list[NormalizationWarning] | None = None
    ) -> dict[str, Any]:
        nonlocal visual_index
        args["provenance"] = build_visual_meta(
            component_name,
            visual_index,
            source=source,
            row_count=row_count,
            generated_at=generated_at,
            approval_request_id=approval_request_id,
            trace_id=trace_id,
            warnings=component_warnings,
        ).to_payload()
        visual_index += 1
        return args

    calls: list[ComponentCall] = [
        ComponentCall(
            "plan_visualization",
            {
                "approach": "Query the Foundry agent connected to Databricks Genie and convert the result into controlled components.",
                "technology": "Azure AI Foundry + Databricks Genie + CopilotKit/AG-UI + Recharts",
                "key_elements": ["real query", "data validation", "controlled KPIs/charts", "executive narrative"],
            },
        ),
        ComponentCall(
            "riskNarrativeCard",
            with_provenance(
                "riskNarrativeCard",
                {
                    "title": "Executive summary",
                    "answer": answer[:1800],
                    "assumptions": ["Data queried through the real Foundry/Genie agent"],
                },
                len(rows),
                warnings,
            ),
        ),
    ]

    lowered_answer = answer.lower()
    if (
        warehouse_name
        and "warehouse" in lowered_answer
        and ("parado" in lowered_answer or "stopped" in lowered_answer or "en proceso" in lowered_answer)
    ):
        status = "query-pending" if "en proceso" in lowered_answer else "needs-start"
        calls.append(ComponentCall("warehouseStatusCard", {"warehouseName": warehouse_name, "status": status}))

    if rows:
        calls.append(
            ComponentCall(
                "insightTable",
                with_provenance("insightTable", {"title": "Details returned by Genie", "columns": headers, "rows": rows[:12]}, len(rows)),
            )
        )

    if rows and label_key and value_key:
        chart_rows = rows[:10]
        numeric_keys = _numeric_keys(headers, rows)
        metric_keys = numeric_keys[:3] or [value_key]
        calls.append(
            ComponentCall(
                "kpiStrip",
                with_provenance(
                    "kpiStrip",
                    {
                        "items": [
                            {
                                "label": _humanize(metric_key),
                                "value": sum(float(row.get(metric_key) or 0) for row in rows),
                                "format": _format_for_key(metric_key),
                                "status": _status_for_metric(metric_key),
                            }
                            for metric_key in metric_keys
                        ]
                        + [{"label": "Rows analyzed", "value": len(rows), "format": "number", "status": "stable"}]
                    },
                    len(rows),
                ),
            )
        )
        top_row = max(rows, key=lambda row: float(row.get(value_key) or 0))
        calls.append(
            ComponentCall(
                "policyBreachCard",
                with_provenance(
                    "policyBreachCard",
                    {
                        "title": f"Focus area: {_humanize(str(top_row.get(label_key, 'segment')))}",
                        "severity": _status_for_metric(value_key),
                        "summary": f"Highest {_humanize(value_key)} among the returned segments.",
                        "metricLabel": _humanize(value_key),
                        "metricValue": top_row.get(value_key, 0),
                        "recommendation": "Review concentration drivers and use follow-up questions for drill-down before taking action.",
                    },
                    len(rows),
                ),
            )
        )
        if len(metric_keys) >= 2:
            calls.append(
                ComponentCall(
                    "metricComparisonChartCard",
                    with_provenance(
                        "metricComparisonChartCard",
                        {
                            "title": f"Metric comparison by {_humanize(label_key)}",
                            "data": chart_rows,
                            "xKey": label_key,
                            "yKeys": metric_keys[:3],
                            "valueFormat": _format_for_key(metric_keys[0]),
                        },
                        len(rows),
                    ),
                )
            )
        if _is_time_like_key(label_key, rows) or any(
            token in question.lower() for token in ["trend", "variation", "compare", "2026-q1", "2026-q2"]
        ):
            calls.append(
                ComponentCall(
                    "lineAreaChartCard",
                    with_provenance(
                        "lineAreaChartCard",
                        {
                            "title": f"Trend for {_humanize(label_key)}",
                            "data": chart_rows,
                            "xKey": label_key,
                            "yKeys": metric_keys[:3],
                            "valueFormat": _format_for_key(metric_keys[0]),
                        },
                        len(rows),
                    ),
                )
            )
        calls.append(
            ComponentCall(
                "donutChartCard",
                with_provenance(
                    "donutChartCard",
                    {
                        "title": f"Share of {_humanize(value_key)}",
                        "data": chart_rows[:8],
                        "labelKey": label_key,
                        "valueKey": value_key,
                        "valueFormat": _format_for_key(value_key),
                    },
                    len(rows),
                ),
            )
        )
        for metric_key in metric_keys[:2]:
            calls.append(
                ComponentCall(
                    "barChartCard",
                    with_provenance(
                        "barChartCard",
                        {
                            "title": f"{_humanize(metric_key)} by {_humanize(label_key)}",
                            "data": chart_rows,
                            "xKey": label_key,
                            "yKey": metric_key,
                            "valueFormat": _format_for_key(metric_key),
                        },
                        len(rows),
                    ),
                )
            )

    calls.append(
        ComponentCall(
            "followUpQuestions",
            {
                "title": "Continue the analysis",
                "questions": build_follow_up_questions(question),
            },
        )
    )

    return calls
