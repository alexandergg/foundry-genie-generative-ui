from __future__ import annotations

import asyncio
import os
import re
import uuid
import warnings
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
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
from src.ui_event_contract import UiEventKind, UiEventPhase, build_ui_event
from src.visualization_mapper import build_dataset_calls

Route = Literal["direct", "dashboard_op", "risk_data"]
GraphNode = Literal["direct_response", "dashboard_op", "run_risk"]

APP_AGENT_NAME = "default"
APP_TITLE = "Risk Exposure Generative UI Agent"
APPROVAL_COMMAND_PREFIX = "approve"
APPROVAL_REJECT_PREFIX = "reject"
APPROVAL_REVISE_PREFIX = "revise"
APPROVAL_TTL_MINUTES = 15
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
data. Never invent risk metrics; if governed data is needed, route through the human
approval flow before querying Genie. Reply in the user's language and keep direct
answers concise.
""".strip()

load_dotenv()
settings = load_settings()
foundry_client = FoundryAgentClient(settings)

ApprovalAction = Literal["approve", "reject", "revise"]
ApprovalStatus = Literal["pending", "used", "rejected", "expired"]


@dataclass
class ApprovalCommand:
    action: ApprovalAction
    request_id: str
    revised_question: str | None = None


@dataclass
class PendingApproval:
    request_id: str
    question: str
    purpose: str
    created_at: datetime
    expires_at: datetime
    audit_id: str
    status: ApprovalStatus = "pending"

    def is_expired(self, now: datetime | None = None) -> bool:
        return (now or datetime.now(timezone.utc)) >= self.expires_at


pending_data_approvals: dict[str, PendingApproval] = {}


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


def _approval_command(message: str) -> ApprovalCommand | None:
    approve_match = re.fullmatch(rf"{APPROVAL_COMMAND_PREFIX}\s+([A-Za-z0-9_-]+)\.?", message.strip())
    if approve_match:
        return ApprovalCommand(action="approve", request_id=approve_match.group(1))

    reject_match = re.fullmatch(rf"{APPROVAL_REJECT_PREFIX}\s+([A-Za-z0-9_-]+)\.?", message.strip())
    if reject_match:
        return ApprovalCommand(action="reject", request_id=reject_match.group(1))

    revise_match = re.fullmatch(rf"{APPROVAL_REVISE_PREFIX}\s+([A-Za-z0-9_-]+)\s*:\s*(.+)", message.strip(), re.DOTALL)
    if revise_match:
        revised_question = revise_match.group(2).strip()
        if revised_question:
            return ApprovalCommand(action="revise", request_id=revise_match.group(1), revised_question=revised_question)
    return None


def _simple_direct_greeting(message: str) -> bool:
    normalized = re.sub(r"[^a-záéíóúüñ]+", " ", message.lower()).strip()
    return normalized in {"hi", "hello", "hey", "hola", "buenas", "buenos dias", "buenas tardes", "buenas noches"}


def _previous_unapproved_user_message(messages: Sequence[AnyMessage]) -> str | None:
    for message in reversed(messages):
        if not isinstance(message, HumanMessage) and getattr(message, "type", None) != "human":
            continue
        text = _message_text(message)
        if not _approval_command(text):
            return text
    return None


def _purge_stale_approvals(now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    max_age = timedelta(minutes=2 * APPROVAL_TTL_MINUTES)
    stale = [
        request_id
        for request_id, approval in pending_data_approvals.items()
        if approval.status != "pending" or (now - approval.created_at) > max_age
    ]
    for request_id in stale:
        del pending_data_approvals[request_id]


def _approval_request(question: str) -> list[AnyMessage]:
    _purge_stale_approvals()
    request_id = uuid.uuid4().hex[:10]
    now = datetime.now(timezone.utc)
    purpose = "Send the question to the Foundry agent to query exposure, claims, brokers or overdue balances."
    pending_data_approvals[request_id] = PendingApproval(
        request_id=request_id,
        question=question,
        purpose=purpose,
        created_at=now,
        expires_at=now + timedelta(minutes=APPROVAL_TTL_MINUTES),
        audit_id=f"approval-{uuid.uuid4().hex[:12]}",
    )
    tool_call_id = f"mcpApprovalCard-{request_id}"
    approval = pending_data_approvals[request_id]
    return [
        AIMessage(content="Approval required before querying governed data."),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": tool_call_id,
                    "name": "mcpApprovalCard",
                    "args": {
                        "requestId": request_id,
                        "question": question,
                        "dataSource": "Databricks Genie Space Risk Exposure through Azure AI Foundry MCP",
                        "purpose": purpose,
                        "approvalCommand": f"{APPROVAL_COMMAND_PREFIX} {request_id}",
                        "rejectCommand": f"{APPROVAL_REJECT_PREFIX} {request_id}",
                        "reviseCommandPrefix": f"{APPROVAL_REVISE_PREFIX} {request_id}:",
                        "expiresAt": approval.expires_at.isoformat().replace("+00:00", "Z"),
                        "auditId": approval.audit_id,
                    },
                }
            ],
        ),
        ToolMessage(content="waiting_for_user_approval", tool_call_id=tool_call_id),
    ]


def _resolve_approved_question(command: ApprovalCommand, messages: Sequence[AnyMessage]) -> str | None:
    approval = pending_data_approvals.get(command.request_id)
    if approval is None:
        return _previous_unapproved_user_message(messages) if command.action == "approve" else None
    if approval.status != "pending":
        return None
    if approval.is_expired():
        approval.status = "expired"
        return None
    if command.action == "reject":
        approval.status = "rejected"
        return None
    approval.status = "used"
    if command.action == "revise" and command.revised_question:
        return command.revised_question
    return approval.question


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
    calls = build_dataset_calls(question, response.answer, trace_id)
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
    if _approval_command(question):
        return {"route": "risk_data"}
    if _simple_direct_greeting(question):
        await _emit_ui_event(
            "reasoning.completed",
            "supervise",
            {"message": "Greeting detected. Answering directly without governed data.", "route": "direct"},
        )
        return {"route": "direct"}

    await _emit_ui_event(
        "reasoning.started",
        "supervise",
        {"message": "Thinking about whether this needs governed risk data…"},
    )
    decision: RouteDecision = await asyncio.to_thread(
        foundry_client.supervise,
        messages,
        bool(_conversation_id(state)),
    )
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
                "message": "Plan: request human approval, then query governed risk data and visualize it.",
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

    if decision.tool == "none" or decision.tool not in {"addVisual", "removeVisual", "changeVisualType", "reorderVisuals", "clearDashboard"}:
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


async def _execute_risk_query(question: str, conversation_id: str | None, approval_request_id: str | None = None) -> dict[str, Any]:
    await _emit_ui_event(
        "query.started",
        "query",
        {"message": "Approval received. Continuing the Azure AI Foundry conversation…", "question": question},
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
        await _emit_ui_event("provenance.attached", "complete", {"message": "Provenance and trace id attached to the result.", "traceId": trace_id})
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

    approval_request_id: str | None = None
    approval_command = _approval_command(question)
    if approval_command:
        approval_request_id = approval_command.request_id
        approved_question = _resolve_approved_question(approval_command, input_messages)
        if approval_command.action == "reject":
            await _emit_ui_event(
                "approval.updated",
                "approval",
                {"message": "Human rejected the governed data request.", "status": "rejected"},
            )
            return _state_update([AIMessage(content="Data access request rejected. I did not query Genie.")], conversation_id)
        if not approved_question:
            return _state_update(
                [
                    AIMessage(
                        content="I cannot use that approval request. It may be missing, expired, rejected or already used. Run the query again to generate a valid authorization."
                    )
                ],
                conversation_id,
            )
        await _emit_ui_event(
            "approval.updated",
            "approval",
            {
                "message": "Human approved the governed data request.",
                "status": "revised" if approval_command.action == "revise" else "approved",
            },
        )
        question = approved_question
    elif settings.require_human_data_approval:
        await _emit_ui_event(
            "approval.requested",
            "approval",
            {"message": "Requesting human approval before querying governed data."},
        )
        return _state_update(_approval_request(question), conversation_id)

    return await _execute_risk_query(question, conversation_id, approval_request_id)


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
