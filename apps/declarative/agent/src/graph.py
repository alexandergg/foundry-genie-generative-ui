"""The declarative agent graph (course L4: A2UI fixed + dynamic schema).

One agent, one component catalog, two schemas:

- FIXED ("executive" / "brief"): the planner fabricates a `renderRiskReport`
  tool call and a real LangGraph ToolNode executes it, returning pre-authored
  A2UI operations. Executing a *real* tool matters: the AG-UI bridge only
  emits discrete TOOL_CALL events from `on_tool_end`, and the runtime's A2UI
  middleware only scans TOOL_CALL_RESULT events.
- DYNAMIC ("freeform"): the runtime injects a `render_a2ui` tool and the
  client ships the catalog's component schemas as context; this agent binds
  the tool and streams, letting the LLM assemble the layout itself — always
  within the same catalog contract.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any, Literal, TypedDict

from copilotkit import LangGraphAGUIAgent, a2ui
from copilotkit.a2ui import a2ui_prompt
from langchain_core.messages import AIMessage, AnyMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from .history import last_user_message, repair_orphan_tool_calls
from .llm import get_chat_model
from .planner import canned_summary, plan_report
from .report_catalog import RENDER_TOOL_NAME, build_report_operations
from .sample_data import DEFAULT_QUARTER, QUARTERS, LayoutId, build_report_view, dataset_json

APP_AGENT_NAME = "default"
RENDER_A2UI_TOOL_NAME = "render_a2ui"

AGENT_DESCRIPTION = """
You are the declarative Generative UI demo agent. You compose governed
risk reports as A2UI surfaces from this app's component catalog, either from
pre-authored layouts (fixed schema) or by assembling the layout yourself
(dynamic schema).
""".strip()

MISSING_DYNAMIC_MESSAGE = (
    "Dynamic A2UI mode is not available: the runtime did not inject the render tool and catalog schema. "
    "Ask for the executive risk report or the compact brief instead (fixed layouts work without it)."
)

# The "ag-ui" channel (hyphenated key) is populated by ag-ui-langgraph with the
# injected tools and the catalog schema context; it must be declared in the
# state schema or LangGraph drops it before the nodes run.
AgentState = TypedDict(
    "AgentState",
    {
        "messages": Annotated[list[AnyMessage], add_messages],
        "report_summary": str,
        "report_mode": Literal["fixed", "dynamic", "none"],
        "tools": list[dict[str, Any]],
        "ag-ui": dict[str, Any],
    },
    total=False,
)


@tool(RENDER_TOOL_NAME)
def render_risk_report(layout: str, quarter: str) -> str:
    """Assemble the pre-authored A2UI report surface for a layout and quarter."""
    layout_id: LayoutId = "brief" if layout == "brief" else "executive"
    safe_quarter = quarter if quarter in QUARTERS else DEFAULT_QUARTER
    view = build_report_view(safe_quarter, layout_id)
    # The middleware detects A2UI operations in the TOOL_CALL_RESULT content,
    # so returning a2ui.render(...) is all it takes to render the surface.
    return a2ui.render(build_report_operations(layout_id, view))


async def compose_report(state: AgentState) -> dict[str, Any]:
    question = last_user_message(state.get("messages", []))
    if not question:
        return {
            "report_mode": "none",
            "messages": [AIMessage(content="Ask for the executive risk report, the compact brief, or a freeform dashboard.")],
        }
    plan = await plan_report(question)
    if plan.layout_id == "freeform":
        return {"report_mode": "dynamic"}
    # The tool call is fabricated deterministically (no LLM tool binding); the
    # ToolNode executes it for real so AG-UI emits discrete TOOL_CALL events.
    tool_call_id = f"{RENDER_TOOL_NAME}-{uuid.uuid4().hex[:8]}"
    request = AIMessage(
        content="",
        tool_calls=[{"id": tool_call_id, "name": RENDER_TOOL_NAME, "args": {"layout": plan.layout_id, "quarter": plan.quarter}}],
    )
    return {"report_mode": "fixed", "messages": [request], "report_summary": plan.summary}


def route_after_compose(state: AgentState) -> str:
    mode = state.get("report_mode")
    if mode == "dynamic":
        return "generate_dynamic"
    if mode == "fixed":
        return "render_report"
    return END


async def summarize_report(state: AgentState) -> dict[str, Any]:
    summary = state.get("report_summary") or canned_summary("executive", DEFAULT_QUARTER)
    return {"messages": [AIMessage(content=summary)]}


def _tool_name(tool_spec: Any) -> str | None:
    if isinstance(tool_spec, dict):
        name = tool_spec.get("name")
        return name if isinstance(name, str) else None
    name = getattr(tool_spec, "name", None)
    return name if isinstance(name, str) else None


def _a2ui_schema_from(ag_ui: dict[str, Any]) -> str | None:
    schema = ag_ui.get("a2ui_schema")
    if isinstance(schema, str) and schema:
        return schema
    # Version-tolerant fallback: ag-ui-langgraph maps the schema context entry
    # to state["ag-ui"]["a2ui_schema"] by matching its exact description, and
    # that wording has drifted across client/bridge versions ("props" vs
    # "properties"). Scan the regular context for the entry instead of relying
    # on the constant.
    for entry in ag_ui.get("context") or []:
        description = entry.get("description") if isinstance(entry, dict) else getattr(entry, "description", "")
        value = entry.get("value") if isinstance(entry, dict) else getattr(entry, "value", "")
        if isinstance(description, str) and description.startswith("A2UI Component Schema") and isinstance(value, str) and value:
            return value
    return None


def _dynamic_system_prompt(schema: str) -> str:
    return (
        f"{a2ui_prompt(schema)}\n\n"
        "## DOMAIN\n"
        "You are composing a governed risk view for this energy-portfolio dataset (amounts in million EUR). "
        "Pick whichever catalog components fit best (Metric, BarChart, PieChart, DataTable, DashboardCard, Badge…), "
        "ground every number in this data and never invent figures. Reply in the user's language.\n"
        f"Dataset rows: {dataset_json()}"
    )


async def generate_dynamic(state: AgentState) -> dict[str, Any]:
    """Dynamic schema: bind the injected render_a2ui tool and let the LLM compose the layout."""
    messages = state.get("messages", [])
    ag_ui = state.get("ag-ui") or {}
    schema = _a2ui_schema_from(ag_ui)
    render_tool = next((t for t in (ag_ui.get("tools") or []) if _tool_name(t) == RENDER_A2UI_TOOL_NAME), None)

    if schema is None or render_tool is None:
        return {"messages": [AIMessage(content=MISSING_DYNAMIC_MESSAGE)]}

    try:
        # Stream (not invoke): the AG-UI bridge turns on_chat_model_stream
        # chunks into TOOL_CALL events, which is what lets the A2UI middleware
        # render the composed surface progressively.
        model = get_chat_model().bind_tools([render_tool])
        history = repair_orphan_tool_calls(list(messages))
        response: Any = None
        async for chunk in model.astream([SystemMessage(content=_dynamic_system_prompt(schema)), *history]):
            response = chunk if response is None else response + chunk
    except Exception as exc:
        return {"messages": [AIMessage(content=f"I could not reach the Foundry model. Safe technical detail: {type(exc).__name__}: {exc}")]}
    if response is None:
        return {"messages": [AIMessage(content="The model returned no output. Try again.")]}
    return {"messages": [response]}


def build_agent_graph() -> Any:
    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("compose_report", compose_report)
    graph_builder.add_node("render_report", ToolNode([render_risk_report]))
    graph_builder.add_node("summarize_report", summarize_report)
    graph_builder.add_node("generate_dynamic", generate_dynamic)
    graph_builder.add_edge(START, "compose_report")
    graph_builder.add_conditional_edges(
        "compose_report",
        route_after_compose,
        {"render_report": "render_report", "generate_dynamic": "generate_dynamic", END: END},
    )
    graph_builder.add_edge("render_report", "summarize_report")
    graph_builder.add_edge("summarize_report", END)
    graph_builder.add_edge("generate_dynamic", END)
    return graph_builder.compile(checkpointer=InMemorySaver())


agent_graph = build_agent_graph()


def build_ag_ui_agent() -> LangGraphAGUIAgent:
    return LangGraphAGUIAgent(name=APP_AGENT_NAME, description=AGENT_DESCRIPTION, graph=agent_graph)
