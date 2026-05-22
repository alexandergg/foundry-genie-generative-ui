from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Any

from .component_registry import validate_component_name
from .normalization import NormalizationWarning, build_dataset_provenance

DEFAULT_PROVENANCE_SOURCE = "Azure AI Foundry + Databricks Genie"


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


def build_follow_up_questions(question: str) -> list[str]:
    """Grounded next-step questions tailored to the asked question's focus."""
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


def build_dataset(
    question: str,
    answer: str,
    trace_id: str | None = None,
    *,
    source: str | None = None,
) -> dict[str, Any] | None:
    """Capture the structured rows behind a Genie answer as a cacheable dataset."""
    headers, rows = extract_markdown_table(answer)
    if not rows:
        headers, rows = extract_bullet_metrics(answer, question)
    if not rows:
        return None
    numeric = set(_numeric_keys(headers, rows))
    columns = [
        {
            "key": header,
            "label": _humanize(header),
            "role": "measure" if header in numeric else "dimension",
            "format": _format_for_key(header) if header in numeric else "text",
        }
        for header in headers
    ]
    dataset_id = f"ds-{trace_id}" if trace_id else f"ds-{uuid.uuid4().hex[:12]}"
    return {
        "id": dataset_id,
        "title": question[:80] or "Genie result",
        "question": question,
        "columns": columns,
        "rows": rows,
        "answer": answer[:1800],
        "traceId": trace_id,
        "provenance": build_dataset_provenance(
            source=source or DEFAULT_PROVENANCE_SOURCE,
            row_count=len(rows),
            trace_id=trace_id,
        ),
    }


def _narrative_visual_call(dataset_id: str) -> ComponentCall:
    """Executive summary card derived from the dataset's narrative answer."""
    return ComponentCall(
        "addVisual",
        {"datasetId": dataset_id, "type": "riskNarrativeCard", "title": "Executive summary"},
    )


def _follow_up_call(question: str) -> ComponentCall:
    """Chat-rendered follow-up chips that drive the next governed query."""
    return ComponentCall(
        "followUpQuestions",
        {"title": "Continue the analysis", "questions": build_follow_up_questions(question)},
    )


def build_dataset_calls(
    question: str,
    answer: str,
    trace_id: str | None = None,
    *,
    source: str | None = None,
) -> list[ComponentCall]:
    """Cache the dataset once, then emit the executive summary plus derived-visual specs."""
    dataset = build_dataset(question, answer, trace_id, source=source)
    if dataset is None:
        # No table behind the answer: cache a narrative-only dataset so the
        # executive summary still renders as a dashboard card.
        dataset_id = f"ds-{trace_id}" if trace_id else f"ds-{uuid.uuid4().hex[:12]}"
        narrative_dataset: dict[str, Any] = {
            "id": dataset_id,
            "title": question[:80] or "Genie result",
            "question": question,
            "columns": [],
            "rows": [],
            "answer": answer[:1800],
            "traceId": trace_id,
            "provenance": build_dataset_provenance(
                source=source or DEFAULT_PROVENANCE_SOURCE,
                row_count=0,
                trace_id=trace_id,
                warnings=[NormalizationWarning("no_structured_rows", "No structured rows were detected; narrative only.")],
            ),
        }
        return [
            ComponentCall("cacheDataset", narrative_dataset),
            _narrative_visual_call(dataset_id),
            _follow_up_call(question),
        ]

    headers = [column["key"] for column in dataset["columns"]]
    label_key, value_key = _pick_keys(headers, dataset["rows"])
    numeric = [column["key"] for column in dataset["columns"] if column["role"] == "measure"]
    # Executive summary first so it pins to the top of the dashboard.
    calls: list[ComponentCall] = [
        ComponentCall("cacheDataset", dataset),
        _narrative_visual_call(dataset["id"]),
    ]

    # Always surface the rows as a table, even when no categorical dimension was
    # detected (all-numeric / ranked results); the charts below still need one.
    table_title = f"Details · {_humanize(label_key)}" if label_key else "Details"
    calls.append(
        ComponentCall(
            "addVisual",
            {"datasetId": dataset["id"], "type": "insightTable", "title": table_title},
        )
    )

    if label_key and value_key:
        calls.append(
            ComponentCall(
                "addVisual",
                {
                    "datasetId": dataset["id"],
                    "type": "barChartCard",
                    "dimension": label_key,
                    "measure": value_key,
                    "title": f"{_humanize(value_key)} by {_humanize(label_key)}",
                },
            )
        )
        if _is_time_like_key(label_key, dataset["rows"]):
            calls.append(
                ComponentCall(
                    "addVisual",
                    {
                        "datasetId": dataset["id"],
                        "type": "lineAreaChartCard",
                        "dimension": label_key,
                        "measure": numeric[:2] or value_key,
                        "title": f"Trend · {_humanize(label_key)}",
                    },
                )
            )
        else:
            calls.append(
                ComponentCall(
                    "addVisual",
                    {
                        "datasetId": dataset["id"],
                        "type": "donutChartCard",
                        "dimension": label_key,
                        "measure": value_key,
                        "title": f"{_humanize(value_key)} share by {_humanize(label_key)}",
                    },
                )
            )

    # Follow-up chips render in chat and drive the next governed query.
    calls.append(_follow_up_call(question))
    return calls
