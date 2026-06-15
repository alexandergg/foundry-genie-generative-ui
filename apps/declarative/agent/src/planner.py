"""Report planner: the only place the LLM steers the fixed-schema flow.

The planner picks a layout (`executive` / `brief` / `freeform`) and a quarter,
and writes a two-sentence summary grounded in pre-computed aggregates. On any
failure it degrades to a keyword heuristic so the fixed demo beats keep
working with no model at all.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal, cast

from langchain_core.messages import HumanMessage, SystemMessage

from .history import content_text
from .llm import get_chat_model
from .sample_data import DEFAULT_QUARTER, QUARTERS, quarter_aggregates

PlanLayout = Literal["executive", "brief", "freeform"]


@dataclass(frozen=True)
class ReportPlan:
    layout_id: PlanLayout
    quarter: str
    summary: str


def canned_summary(layout_id: PlanLayout, quarter: str) -> str:
    aggregates = quarter_aggregates()[quarter]
    label = "Executive risk report" if layout_id == "executive" else "Risk brief"
    return (
        f"{label} for {quarter}: total exposure {aggregates['exposure']}, claims {aggregates['claims']}, "
        f"overdue balance {aggregates['overdue']}. The layout was assembled from the fixed A2UI catalog "
        "and the data model was streamed by path."
    )


def _planner_prompt(question: str) -> str:
    return (
        "You plan a governed risk report rendered as A2UI from this app's component catalog. "
        "Return ONLY a valid JSON object with keys: layout, quarter, summary. "
        'layout must be "executive" (full fixed report: KPIs, bar chart, ranked exposures, country table), '
        '"brief" (compact fixed brief: KPIs, pie chart, ranked exposures), or "freeform" (the user wants you to '
        "compose/improvise the layout yourself, e.g. 'your way', 'a tu manera', 'any layout', 'custom dashboard'). "
        f"quarter must be one of {list(QUARTERS)}. "
        "summary must be exactly two concise sentences in the user's language describing the chosen quarter, "
        "using ONLY the aggregates below — never invent numbers. For freeform, summary may be an empty string. "
        f"Aggregates by quarter (M EUR): {json.dumps(quarter_aggregates(), ensure_ascii=False)}\n"
        f"User request: {question}"
    )


def _json_object_from_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end >= start:
        cleaned = cleaned[start : end + 1]
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object from the report planner.")
    return cast(dict[str, Any], payload)


def parse_report_plan(text: str) -> ReportPlan:
    payload = _json_object_from_text(text)
    layout_raw = payload.get("layout")
    layout_id: PlanLayout = layout_raw if layout_raw in ("executive", "brief", "freeform") else "executive"
    quarter_raw = payload.get("quarter")
    quarter = quarter_raw if isinstance(quarter_raw, str) and quarter_raw in QUARTERS else DEFAULT_QUARTER
    summary_raw = payload.get("summary")
    if layout_id == "freeform":
        summary = summary_raw if isinstance(summary_raw, str) else ""
    else:
        summary = summary_raw if isinstance(summary_raw, str) and summary_raw.strip() else canned_summary(layout_id, quarter)
    return ReportPlan(layout_id=layout_id, quarter=quarter, summary=summary)


def heuristic_plan(question: str) -> ReportPlan:
    """Keyword fallback so the fixed demo beats keep working with no model at all.

    Never picks freeform: the dynamic schema needs the model anyway.
    """
    lowered = question.lower()
    layout_id: PlanLayout = "brief" if any(marker in lowered for marker in ("brief", "compact", "breve", "compacto")) else "executive"
    quarter = next((q for q in QUARTERS if q.lower() in lowered or q.split("-")[1].lower() in lowered), DEFAULT_QUARTER)
    return ReportPlan(layout_id=layout_id, quarter=quarter, summary=canned_summary(layout_id, quarter))


async def plan_report(question: str) -> ReportPlan:
    """Ask the LLM for layout + quarter + summary; degrade to a deterministic plan on any failure."""
    try:
        model = get_chat_model()
        response = await model.ainvoke([SystemMessage(content=_planner_prompt(question)), HumanMessage(content=question)])
        return parse_report_plan(content_text(response.content))
    except Exception:
        return heuristic_plan(question)
