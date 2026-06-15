from __future__ import annotations

import asyncio
import os
import uuid
import warnings
from collections.abc import Sequence
from contextlib import suppress
from typing import Annotated, Any, Literal, TypedDict

from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from copilotkit import LangGraphAGUIAgent
from dotenv import load_dotenv
from fastapi import FastAPI
from langchain_core.callbacks import adispatch_custom_event
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from src.config import load_settings
from src.dashboard_context import extract_dashboard_context
from src.foundry_agent_client import CONVERSATION_ID_KEY, DashboardOpDecision, FoundryAgentClient, FoundryAgentResponse, RouteDecision
from src.observability import build_trace_callbacks
from src.ui_event_contract import UiEventKind, UiEventPhase, build_ui_event
from src.visualization_mapper import build_dataset_calls

Route = Literal["direct", "dashboard_op", "risk_data"]
GraphNode = Literal["direct_response", "dashboard_op", "run_risk"]

APP_AGENT_NAME = "default"
# gen_ai.agent.id stamped on emitted spans — match the deployed Foundry agent name.
TRACE_AGENT_ID = "risk-exposure-ag-ui-hosted"
APP_TITLE = "Risk Exposure Generative UI Agent"
FOUNDRY_CONVERSATION_KEY = CONVERSATION_ID_KEY

NODE_SUPERVISE = "supervise_request"
NODE_DIRECT = "direct_response"
NODE_RISK = "run_risk"
NODE_DASHBOARD = "dashboard_op"

HOSTED_AGENT_PROMPT = """
You are Genie Risk Copilot, the hosted AG-UI orchestrator for this demo.
Use Microsoft Foundry Agent Service conversation history as the source of short-term
context. Answer directly for greetings, app help, capability questions, conceptual
explanations, setup questions, UI questions, and follow-ups that can be answered from
the active Foundry conversation or prior Genie results already in that conversation.
Use Databricks Genie only for concrete risk analytics questions that need new governed
data. Never invent risk metrics; when governed data is needed, route through the governed
risk-data flow to query Genie. Reply in the user's language and keep direct
answers concise.
""".strip()

load_dotenv()
settings = load_settings()
foundry_client = FoundryAgentClient(settings)


class AgentState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    route: Route
    azure_ai_agents_conversation_id: str | None


def _message_text(message: AnyMessage) -> str:
    content = message.content
    return content if isinstance(content, str) else str(content)


def _last_user_message(messages: Sequence[AnyMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage) or getattr(message, "type", None) == "human":
            return _message_text(message)
    return ""


def _conversation_id(state: AgentState) -> str | None:
    return state.get("azure_ai_agents_conversation_id")


def _state_update(messages: list[AnyMessage], conversation_id: str | None = None) -> dict[str, Any]:
    update: dict[str, Any] = {"messages": messages}
    if conversation_id is not None:
        update[CONVERSATION_ID_KEY] = conversation_id
    return update


def _component_message(name: str, args: dict[str, Any]) -> list[AnyMessage]:
    tool_call_id = f"{name}-{uuid.uuid4().hex[:8]}"
    return [
        AIMessage(content="", tool_calls=[{"id": tool_call_id, "name": name, "args": args}]),
        ToolMessage(content="rendered", tool_call_id=tool_call_id),
    ]


def _render_component_messages(
    question: str,
    response: FoundryAgentResponse,
    trace_id: str | None = None,
) -> list[AnyMessage]:
    messages: list[AnyMessage] = []
    calls = build_dataset_calls(
        question,
        response.answer,
        trace_id,
        source=settings.databricks_sql_warehouse_name or None,
    )
    for call in calls:
        messages.extend(_component_message(call.name, call.args))
    return messages


def _safe_error_message(prefix: str, exc: Exception) -> AIMessage:
    return AIMessage(content=f"{prefix} Safe technical detail: {type(exc).__name__}: {exc}")


async def _emit_ui_event(kind: UiEventKind, phase: UiEventPhase, payload: dict[str, Any]) -> None:
    event = build_ui_event(kind, phase, payload)
    with suppress(RuntimeError):
        await adispatch_custom_event("risk_ui_event", event.to_payload())


async def supervise_request(state: AgentState) -> dict[str, Any]:
    messages = state.get("messages", [])
    question = _last_user_message(messages)
    if not question:
        return {"route": "direct"}

    await _emit_ui_event(
        "reasoning.started",
        "supervise",
        {"message": "Thinking about whether this needs governed risk data…"},
    )
    try:
        decision: RouteDecision = await asyncio.to_thread(
            foundry_client.supervise,
            messages,
            bool(_conversation_id(state)),
        )
    except Exception as exc:
        # The supervisor is a network LLM call and this is the graph entry node:
        # an unhandled error here fails the entire run. Fall back to a direct
        # response (every downstream node handles failure safely) so a transient
        # Foundry/Azure error on a trivial message can't kill the whole turn.
        await _emit_ui_event(
            "reasoning.completed",
            "supervise",
            {
                "message": "Supervisor routing unavailable; answering directly.",
                "route": "direct",
                "errorType": type(exc).__name__,
            },
        )
        return {"route": "direct"}
    await _emit_ui_event(
        "reasoning.completed",
        "supervise",
        {
            "message": f"Route selected: {'governed data flow' if decision.route == 'risk_data' else 'direct response'}.",
            "route": decision.route,
            "rationale": decision.rationale,
        },
    )
    if decision.route == "risk_data":
        await _emit_ui_event(
            "plan.created",
            "supervise",
            {
                "message": "Plan: query governed risk data and visualize it.",
                "rationale": decision.rationale,
            },
        )
    return {"route": decision.route}


def route_supervisor_decision(state: AgentState) -> GraphNode:
    route = state.get("route")
    if route == "risk_data":
        return "run_risk"
    if route == "dashboard_op":
        return "dashboard_op"
    return "direct_response"


async def dashboard_op(state: AgentState) -> dict[str, Any]:
    messages = state.get("messages", [])
    question = _last_user_message(messages)
    conversation_id = _conversation_id(state)
    context = extract_dashboard_context(messages)

    if not context["datasets"]:
        return _state_update(
            [AIMessage(content="There is no data on the dashboard yet. Ask a risk question first, then I can add or change visuals.")],
            conversation_id,
        )

    await _emit_ui_event(
        "reasoning.started",
        "supervise",
        {"message": "Updating the dashboard from already-retrieved data (no new Genie query)."},
    )
    try:
        decision: DashboardOpDecision = await asyncio.to_thread(foundry_client.decide_dashboard_op, question, context)
    except Exception as exc:
        await _emit_ui_event("error.safe", "error", {"message": "Could not decide the dashboard update.", "errorType": type(exc).__name__})
        return _state_update([_safe_error_message("I could not update the dashboard.", exc)], conversation_id)

    if decision.tool == "none" or decision.tool not in {
        "addVisual",
        "removeVisual",
        "changeVisualType",
        "reorderVisuals",
        "clearDashboard",
        "spotlightVisual",
        "setPresentationMode",
    }:
        return _state_update([AIMessage(content=decision.message or "I could not map that to a dashboard action.")], conversation_id)

    await _emit_ui_event(
        "visualization.proposed",
        "visualize",
        {"message": decision.message or f"Applying {decision.tool} to the dashboard."},
    )
    out_messages = _component_message(decision.tool, decision.args)
    await _emit_ui_event("visualization.rendered", "visualize", {"message": "Dashboard updated from cached data."})
    out_messages.append(AIMessage(content=decision.message or "Updated the dashboard from the data already retrieved."))
    return _state_update(out_messages, conversation_id)


async def direct_response(state: AgentState) -> dict[str, Any]:
    question = _last_user_message(state.get("messages", []))
    conversation_id = _conversation_id(state)
    if not question:
        return _state_update(
            [AIMessage(content="What would you like to analyze or discuss about the Risk Exposure demo?")], conversation_id
        )

    try:
        response = await asyncio.to_thread(foundry_client.answer_direct, question, conversation_id)
        return _state_update([AIMessage(content=response.answer)], response.conversation_id or conversation_id)
    except Exception as exc:
        return _state_update(
            [
                _safe_error_message(
                    "I could not complete the direct Foundry response. Check Azure authentication and hosted agent configuration.",
                    exc,
                )
            ],
            conversation_id,
        )


async def _execute_risk_query(question: str, conversation_id: str | None) -> dict[str, Any]:
    await _emit_ui_event(
        "query.started",
        "query",
        {"message": "Querying the Azure AI Foundry conversation for governed data…", "question": question},
    )
    await _emit_ui_event(
        "normalization.started",
        "normalize",
        {"message": "Foundry will use its active conversation and call Genie only if new governed data is required."},
    )

    messages: list[AnyMessage] = []
    trace_id = f"risk-{uuid.uuid4().hex[:12]}"
    try:
        response = await asyncio.to_thread(foundry_client.ask, question, conversation_id)
        await _emit_ui_event("normalization.completed", "normalize", {"message": "Genie results normalized into governed records."})
        await _emit_ui_event("query.completed", "query", {"message": "Governed query completed.", "traceId": trace_id})
        await _emit_ui_event("visualization.proposed", "visualize", {"message": "Proposing controlled visualizations for the result."})
        messages.extend(_render_component_messages(question, response, trace_id))
        await _emit_ui_event("visualization.rendered", "visualize", {"message": "Controlled visualizations rendered."})
        await _emit_ui_event("followups.suggested", "complete", {"message": "Suggested grounded follow-up questions."})
        await _emit_ui_event(
            "provenance.attached", "complete", {"message": "Provenance and trace id attached to the result.", "traceId": trace_id}
        )
        messages.append(AIMessage(content="I used the real Genie result through the active Foundry conversation to compose the view."))
        conversation_id = response.conversation_id or conversation_id
    except Exception as exc:
        await _emit_ui_event("error.safe", "error", {"message": "Foundry/Genie query failed safely.", "errorType": type(exc).__name__})
        messages.append(
            _safe_error_message(
                "I could not complete the real query against Foundry/Genie. Check Azure CLI authentication, Databricks permissions and SQL Warehouse availability.",
                exc,
            )
        )
    return _state_update(messages, conversation_id)


async def run_risk(state: AgentState) -> dict[str, Any]:
    input_messages = state.get("messages", [])
    question = _last_user_message(input_messages)
    conversation_id = _conversation_id(state)
    if not question:
        return _state_update(
            [AIMessage(content="What would you like to analyze about exposure, claims, brokers or overdue balances?")], conversation_id
        )

    return await _execute_risk_query(question, conversation_id)


def build_agent_graph() -> Any:
    graph_builder = StateGraph(AgentState)
    graph_builder.add_node(NODE_SUPERVISE, supervise_request)
    graph_builder.add_node(NODE_DIRECT, direct_response)
    graph_builder.add_node(NODE_RISK, run_risk)
    graph_builder.add_node(NODE_DASHBOARD, dashboard_op)
    graph_builder.add_edge(START, NODE_SUPERVISE)
    graph_builder.add_conditional_edges(
        NODE_SUPERVISE,
        route_supervisor_decision,
        {NODE_DIRECT: NODE_DIRECT, NODE_RISK: NODE_RISK, NODE_DASHBOARD: NODE_DASHBOARD},
    )
    graph_builder.add_edge(NODE_DIRECT, END)
    graph_builder.add_edge(NODE_RISK, END)
    graph_builder.add_edge(NODE_DASHBOARD, END)
    return graph_builder.compile(checkpointer=InMemorySaver())


def build_ag_ui_agent() -> LangGraphAGUIAgent:
    return LangGraphAGUIAgent(
        name=APP_AGENT_NAME,
        description=HOSTED_AGENT_PROMPT,
        graph=agent_graph,
        config={"callbacks": build_trace_callbacks(TRACE_AGENT_ID)},
    )


agent_graph = build_agent_graph()
app = FastAPI(title=APP_TITLE)


@app.get("/health")
def health() -> dict[str, str | None]:
    return {
        "status": "ok",
        "foundryAgent": settings.agent_name,
        "foundryAgentVersion": settings.agent_version,
        "warehouse": settings.databricks_sql_warehouse_name,
    }


add_langgraph_fastapi_endpoint(
    app=app,
    agent=build_ag_ui_agent(),
    path="/",
)

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8123")), reload=True)
