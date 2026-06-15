"""The open-ended agent graph (course L5: MCP Apps + sandboxed UI).

One node at the far end of the spectrum. The runtime/client inject open-ended
frontend tools into every run — `generateSandboxedUi` (arbitrary HTML/CSS/JS
rendered in a sandboxed iframe) when the runtime enables `openGenerativeUI`,
plus any MCP App tools (e.g. Excalidraw) the runtime discovers. This agent
simply binds ALL injected tools to the Foundry model and streams; the runtime
middlewares render the sandboxed surface or embed the MCP app and synthesize
tool results.

Contrast with the declarative demo: here nothing bounds the output but the
tools' own contracts — which is the point (and the governance caveat) of
this band.
"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from copilotkit import LangGraphAGUIAgent
from langchain_core.messages import AIMessage, AnyMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from .history import repair_orphan_tool_calls
from .llm import get_chat_model
from .observability import build_trace_callbacks
from .sample_data import domain_preamble

APP_AGENT_NAME = "default"
# gen_ai.agent.id stamped on emitted spans — match the deployed Foundry agent name.
TRACE_AGENT_ID = "risk-open-ended-ui-hosted"
SANDBOXED_UI_TOOL_NAME = "generateSandboxedUi"

AGENT_DESCRIPTION = """
You are the open-ended Generative UI demo agent. You build arbitrary UI for an
energy-portfolio risk dataset using the injected open-ended tools (sandboxed
UI generation and MCP Apps such as Excalidraw).
""".strip()

MISSING_TOOLS_MESSAGE = (
    "Open-ended mode is not enabled: no frontend tools were injected into this run. "
    "Check that /api/copilotkit configures `openGenerativeUI: true` (and optionally `mcpApps`)."
)

TOOL_GUIDANCE = """
## TOOL GUIDANCE
- For widgets, dashboards, animations or any rich visual surface: call generateSandboxedUi
  (follow its parameter order; you may load CDN libraries like Chart.js in the HTML head).
- CRITICAL for generateSandboxedUi: write the REAL data values inline in the HTML markup —
  never placeholders like "—" or 0.0% to be filled in by JavaScript later. The page must look
  complete and correct even if no JavaScript runs. Use JS only for interactivity and animation
  on top of already-correct content.
- Any initialization code must be invoked from jsExpressions (they run after the HTML is
  injected). NEVER rely on DOMContentLoaded or window.onload — those events may have already
  fired and your handler will never run.
- For whiteboards, diagrams or sketches: use the Excalidraw MCP tools when available.
- Only answer in plain text when the user explicitly asks for text.
- After calling a tool, do NOT repeat the data in text — just confirm what was rendered.
""".strip()

# The "ag-ui" channel (hyphenated key) is populated by ag-ui-langgraph with the
# forwarded tools and context; it must be declared in the state schema or
# LangGraph drops it before the node runs.
AgentState = TypedDict(
    "AgentState",
    {
        "messages": Annotated[list[AnyMessage], add_messages],
        "tools": list[dict[str, Any]],
        "ag-ui": dict[str, Any],
    },
    total=False,
)


def _tool_name(tool: Any) -> str | None:
    if isinstance(tool, dict):
        name = tool.get("name")
        return name if isinstance(name, str) else None
    name = getattr(tool, "name", None)
    return name if isinstance(name, str) else None


def _context_notes(context: list[Any]) -> str:
    lines: list[str] = []
    for entry in context:
        description = entry.get("description") if isinstance(entry, dict) else getattr(entry, "description", "")
        value = entry.get("value") if isinstance(entry, dict) else getattr(entry, "value", "")
        if description or value:
            lines.append(f"- {description}: {value}")
    return "\n".join(lines)


def build_system_prompt(context: list[Any]) -> str:
    sections = [domain_preamble(), TOOL_GUIDANCE]
    notes = _context_notes(context)
    if notes:
        sections.append(f"## ADDITIONAL CONTEXT\n{notes}")
    return "\n\n".join(sections)


async def generate_ui(state: AgentState) -> dict[str, Any]:
    messages = state.get("messages", [])
    ag_ui = state.get("ag-ui") or {}
    tools = [tool for tool in (ag_ui.get("tools") or []) if _tool_name(tool)]

    if not tools:
        return {"messages": [AIMessage(content=MISSING_TOOLS_MESSAGE)]}

    try:
        # Bind EVERY injected tool (sandboxed UI + MCP app tools) and stream:
        # the AG-UI bridge turns on_chat_model_stream chunks into TOOL_CALL
        # events, which is what lets the middlewares render progressively.
        model = get_chat_model().bind_tools(tools)
        history = repair_orphan_tool_calls(list(messages))
        response: Any = None
        async for chunk in model.astream([SystemMessage(content=build_system_prompt(ag_ui.get("context") or [])), *history]):
            response = chunk if response is None else response + chunk
    except Exception as exc:
        return {"messages": [AIMessage(content=f"I could not reach the Foundry model. Safe technical detail: {type(exc).__name__}: {exc}")]}
    if response is None:
        return {"messages": [AIMessage(content="The model returned no output. Try again.")]}
    return {"messages": [response]}


def build_agent_graph() -> Any:
    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("generate_ui", generate_ui)
    graph_builder.add_edge(START, "generate_ui")
    graph_builder.add_edge("generate_ui", END)
    return graph_builder.compile(checkpointer=InMemorySaver())


agent_graph = build_agent_graph()


def build_ag_ui_agent() -> LangGraphAGUIAgent:
    return LangGraphAGUIAgent(
        name=APP_AGENT_NAME,
        description=AGENT_DESCRIPTION,
        graph=agent_graph,
        config={"callbacks": build_trace_callbacks(TRACE_AGENT_ID)},
    )
