from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage

from src.dashboard_context import extract_dashboard_context, visual_id_for


def _ai_tool_call(name: str, args: dict[str, Any]) -> AIMessage:
    return AIMessage(content="", tool_calls=[{"id": f"{name}-x", "name": name, "args": args}])


def test_visual_id_matches_client_formula() -> None:
    args = {"datasetId": "ds-1", "type": "donutChartCard", "dimension": "Country", "measure": "Exposure"}
    assert visual_id_for(args) == "vis-ds-1-donutChartCard-Country-Exposure"
    arr = {"datasetId": "ds-1", "type": "metricComparisonChartCard", "dimension": "Country", "measure": ["a", "b"]}
    assert visual_id_for(arr) == "vis-ds-1-metricComparisonChartCard-Country-a_b"


def test_extract_collects_dataset_and_visuals() -> None:
    messages: list[AnyMessage] = [
        HumanMessage(content="exposure by country"),
        _ai_tool_call(
            "cacheDataset",
            {
                "id": "ds-1",
                "title": "Exposure",
                "columns": [{"key": "Country", "role": "dimension"}, {"key": "Exposure", "role": "measure"}],
                "rows": [],
            },
        ),
        _ai_tool_call(
            "addVisual", {"datasetId": "ds-1", "type": "barChartCard", "dimension": "Country", "measure": "Exposure", "title": "Bar"}
        ),
        _ai_tool_call(
            "addVisual", {"datasetId": "ds-1", "type": "donutChartCard", "dimension": "Country", "measure": "Exposure", "title": "Donut"}
        ),
    ]
    ctx = extract_dashboard_context(messages)
    assert [d["id"] for d in ctx["datasets"]] == ["ds-1"]
    assert ctx["datasets"][0]["columns"] == [{"key": "Country", "role": "dimension"}, {"key": "Exposure", "role": "measure"}]
    assert {v["type"] for v in ctx["visuals"]} == {"barChartCard", "donutChartCard"}


def test_extract_applies_remove_and_change_type() -> None:
    messages: list[AnyMessage] = [
        _ai_tool_call("cacheDataset", {"id": "ds-1", "title": "T", "columns": [], "rows": []}),
        _ai_tool_call(
            "addVisual", {"datasetId": "ds-1", "type": "barChartCard", "dimension": "Country", "measure": "Exposure", "title": "Bar"}
        ),
        _ai_tool_call(
            "addVisual", {"datasetId": "ds-1", "type": "donutChartCard", "dimension": "Country", "measure": "Exposure", "title": "Donut"}
        ),
        _ai_tool_call("removeVisual", {"id": "vis-ds-1-barChartCard-Country-Exposure"}),
        _ai_tool_call("changeVisualType", {"id": "vis-ds-1-donutChartCard-Country-Exposure", "type": "lineAreaChartCard"}),
    ]
    ctx = extract_dashboard_context(messages)
    assert len(ctx["visuals"]) == 1
    assert ctx["visuals"][0]["type"] == "lineAreaChartCard"


def test_clear_empties_visuals() -> None:
    messages: list[AnyMessage] = [
        _ai_tool_call("cacheDataset", {"id": "ds-1", "title": "T", "columns": [], "rows": []}),
        _ai_tool_call(
            "addVisual", {"datasetId": "ds-1", "type": "barChartCard", "dimension": "Country", "measure": "Exposure", "title": "Bar"}
        ),
        _ai_tool_call("clearDashboard", {}),
    ]
    ctx = extract_dashboard_context(messages)
    assert ctx["visuals"] == []
    assert len(ctx["datasets"]) == 1
