from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, SystemMessage, ToolMessage

from src import graph as graph_module
from src import planner as planner_module
from src.graph import (
    MISSING_DYNAMIC_MESSAGE,
    RENDER_A2UI_TOOL_NAME,
    AgentState,
    agent_graph,
    compose_report,
    generate_dynamic,
    render_risk_report,
)
from src.planner import ReportPlan, parse_report_plan, plan_report
from src.report_catalog import RENDER_TOOL_NAME, RISK_CATALOG_ID
from src.sample_data import DEFAULT_QUARTER

RENDER_A2UI_TOOL = {
    "name": RENDER_A2UI_TOOL_NAME,
    "description": "Render a dynamic A2UI surface.",
    "parameters": {"type": "object", "properties": {"surfaceId": {"type": "string"}}},
}


async def _fixed_plan(question: str) -> ReportPlan:
    return ReportPlan(layout_id="executive", quarter="2026-Q2", summary="Two sentences.")


async def _freeform_plan(question: str) -> ReportPlan:
    return ReportPlan(layout_id="freeform", quarter=DEFAULT_QUARTER, summary="")


class FakeChatModel:
    def __init__(self) -> None:
        self.bound_tools: list[Any] = []
        self.received_messages: list[Any] = []

    def bind_tools(self, tools: list[Any]) -> FakeChatModel:
        self.bound_tools = tools
        return self

    async def astream(self, messages: list[Any]) -> AsyncIterator[AIMessageChunk]:
        self.received_messages = messages
        yield AIMessageChunk(
            content="",
            tool_call_chunks=[
                {"id": "call-1", "name": RENDER_A2UI_TOOL_NAME, "args": '{"surfaceId": "composed"}', "index": 0, "type": "tool_call_chunk"}
            ],
        )


async def test_compose_report_fabricates_the_render_tool_call(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(graph_module, "plan_report", _fixed_plan)
    result = await compose_report({"messages": [HumanMessage(content="Give me the executive risk report")]})

    assert result["report_mode"] == "fixed"
    request = result["messages"][0]
    assert isinstance(request, AIMessage)
    assert request.tool_calls[0]["name"] == RENDER_TOOL_NAME
    assert request.tool_calls[0]["args"] == {"layout": "executive", "quarter": "2026-Q2"}
    assert result["report_summary"] == "Two sentences."


async def test_compose_report_routes_freeform_to_dynamic(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(graph_module, "plan_report", _freeform_plan)
    result = await compose_report({"messages": [HumanMessage(content="Compose a dashboard your way")]})
    assert result == {"report_mode": "dynamic"}


def test_render_tool_returns_a2ui_operations_with_custom_catalog() -> None:
    rendered = render_risk_report.invoke({"layout": "brief", "quarter": "2026-Q1"})
    operations = json.loads(rendered)["a2ui_operations"]
    assert [next(key for key in op if key != "version") for op in operations] == ["createSurface", "updateComponents", "updateDataModel"]
    assert operations[0]["createSurface"] == {"surfaceId": "risk-report-brief", "catalogId": RISK_CATALOG_ID}

    clamped = json.loads(render_risk_report.invoke({"layout": "weird", "quarter": "1999-Q9"}))
    assert clamped["a2ui_operations"][0]["createSurface"]["surfaceId"] == "risk-report-executive"


async def test_graph_executes_tool_and_closes_with_summary(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(graph_module, "plan_report", _fixed_plan)
    result = await agent_graph.ainvoke(
        {"messages": [HumanMessage(content="Give me the executive risk report")]},
        config={"configurable": {"thread_id": "test-fixed"}},
    )

    messages = result["messages"]
    tool_results = [m for m in messages if isinstance(m, ToolMessage)]
    assert len(tool_results) == 1
    assert "a2ui_operations" in str(tool_results[0].content)

    final = messages[-1]
    assert isinstance(final, AIMessage)
    assert final.content == "Two sentences."


async def test_graph_routes_freeform_through_generate_dynamic(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    fake = FakeChatModel()
    monkeypatch.setattr(graph_module, "plan_report", _freeform_plan)
    monkeypatch.setattr(graph_module, "get_chat_model", lambda: fake)

    # Schema arrives via the regular context here (the ag-ui-langgraph constant
    # drifted across versions), exercising the version-tolerant fallback.
    result = await agent_graph.ainvoke(
        {
            "messages": [HumanMessage(content="Compose a dashboard your way")],
            "ag-ui": {
                "tools": [RENDER_A2UI_TOOL],
                "context": [{"description": "A2UI Component Schema — available components.", "value": '[{"name": "Metric"}]'}],
            },
        },
        config={"configurable": {"thread_id": "test-dynamic"}},
    )

    assert [tool["name"] for tool in fake.bound_tools] == [RENDER_A2UI_TOOL_NAME]
    system = fake.received_messages[0]
    assert isinstance(system, SystemMessage)
    assert '[{"name": "Metric"}]' in str(system.content)  # catalog schema from client context
    assert "Spain" in str(system.content)  # dataset grounding

    final = result["messages"][-1]
    assert isinstance(final, AIMessage)
    assert final.tool_calls and final.tool_calls[0]["name"] == RENDER_A2UI_TOOL_NAME


def test_catalog_id_resolves_from_shipped_schema_then_falls_back() -> None:
    from src.graph import _catalog_id_from

    # Client may ship the catalog as a wrapped schema object — honor its id.
    assert _catalog_id_from({"a2ui_schema": '{"catalogId": "copilotkit://custom", "components": []}'}) == "copilotkit://custom"
    # A bare components array carries no id — fall back to this app's catalog.
    assert _catalog_id_from({"a2ui_schema": '[{"name": "Metric"}]'}) == RISK_CATALOG_ID
    # Nothing shipped at all — still bind to the app's catalog, never the basic one.
    assert _catalog_id_from({}) == RISK_CATALOG_ID


async def test_generate_dynamic_instructs_model_to_bind_custom_catalog(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    fake = FakeChatModel()
    monkeypatch.setattr(graph_module, "get_chat_model", lambda: fake)

    state: AgentState = {
        "messages": [HumanMessage(content="Compose a dashboard your way")],
        "ag-ui": {"a2ui_schema": '[{"name": "Metric"}]', "tools": [RENDER_A2UI_TOOL]},
    }
    await generate_dynamic(state)

    system = fake.received_messages[0]
    assert isinstance(system, SystemMessage)
    # The @ag-ui/a2ui-middleware stamps the surface catalog from the model's
    # render_a2ui "catalogId" arg, defaulting to the basic catalog when absent —
    # which the frontend never registers (includeBasicCatalog: false), so the
    # surface fails with "Catalog not found". The prompt must pin the real id.
    assert RISK_CATALOG_ID in str(system.content)
    assert "catalogId" in str(system.content)


async def test_generate_dynamic_degrades_without_injected_tool() -> None:
    state: AgentState = {"messages": [HumanMessage(content="Compose a dashboard your way")]}
    result = await generate_dynamic(state)
    assert result["messages"][0].content == MISSING_DYNAMIC_MESSAGE


async def test_generate_dynamic_repairs_orphan_tool_calls(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    fake = FakeChatModel()
    monkeypatch.setattr(graph_module, "get_chat_model", lambda: fake)

    state: AgentState = {
        "messages": [
            HumanMessage(content="Compose a dashboard your way"),
            AIMessage(content="", tool_calls=[{"id": "call-old", "name": RENDER_A2UI_TOOL_NAME, "args": {}}]),
            HumanMessage(content="Make it more compact"),
        ],
        "ag-ui": {"a2ui_schema": '[{"name": "Metric"}]', "tools": [RENDER_A2UI_TOOL]},
    }
    await generate_dynamic(state)

    sent = fake.received_messages
    orphan_index = next(i for i, m in enumerate(sent) if isinstance(m, AIMessage) and m.tool_calls)
    follow_up = sent[orphan_index + 1]
    assert isinstance(follow_up, ToolMessage)
    assert follow_up.tool_call_id == "call-old"


async def test_compose_report_without_question_prompts_for_one() -> None:
    result = await compose_report({"messages": []})
    assert result["report_mode"] == "none"
    assert "risk report" in str(result["messages"][0].content)


async def test_plan_report_degrades_to_deterministic_fallback(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def boom() -> None:
        raise RuntimeError("no model configured")

    monkeypatch.setattr(planner_module, "get_chat_model", boom)
    plan = await plan_report("anything")
    assert plan.layout_id == "executive"
    assert plan.quarter == DEFAULT_QUARTER
    assert "total exposure" in plan.summary

    # Keyword heuristic keeps both fixed demo beats working offline (never freeform).
    brief = await plan_report("Show the compact risk brief for 2026-Q1 instead")
    assert brief.layout_id == "brief"
    assert brief.quarter == "2026-Q1"


def test_parse_report_plan_clamps_invalid_values() -> None:
    plan = parse_report_plan('{"layout": "weird", "quarter": "1999-Q9", "summary": "  "}')
    assert plan.layout_id == "executive"
    assert plan.quarter == DEFAULT_QUARTER
    assert plan.summary  # canned summary filled in

    freeform = parse_report_plan('{"layout": "freeform", "quarter": "2026-Q1", "summary": ""}')
    assert freeform.layout_id == "freeform"
    assert freeform.summary == ""
