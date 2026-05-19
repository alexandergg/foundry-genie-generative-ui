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

from src.config import Settings, load_settings
from src.foundry_agent_client import CONVERSATION_ID_KEY, FoundryAgentClient, FoundryAgentResponse, RouteDecision
from src.visualization_mapper import build_component_calls

Route = Literal["direct", "risk_data"]
GraphNode = Literal["direct_response", "run_risk"]

APP_AGENT_NAME = "default"
APP_TITLE = "Risk Exposure Generative UI Agent"
APPROVAL_COMMAND_PREFIX = "approve"
FOUNDRY_CONVERSATION_KEY = CONVERSATION_ID_KEY

NODE_SUPERVISE = "supervise_request"
NODE_DIRECT = "direct_response"
NODE_RISK = "run_risk"

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
pending_data_approvals: dict[str, str] = {}


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


def _approval_token(message: str) -> str | None:
    if not message.startswith(APPROVAL_COMMAND_PREFIX):
        return None
    token = message.removeprefix(APPROVAL_COMMAND_PREFIX).strip().strip(".")
    return token or None


def _previous_unapproved_user_message(messages: Sequence[AnyMessage]) -> str | None:
    for message in reversed(messages):
        if not isinstance(message, HumanMessage) and getattr(message, "type", None) != "human":
            continue
        text = _message_text(message)
        if not _approval_token(text):
            return text
    return None


def _approval_request(question: str) -> list[AnyMessage]:
    request_id = uuid.uuid4().hex[:10]
    pending_data_approvals[request_id] = question
    tool_call_id = f"mcpApprovalCard-{request_id}"
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
                        "purpose": "Send the question to the Foundry agent to query exposure, claims, brokers or overdue balances.",
                        "approvalCommand": f"{APPROVAL_COMMAND_PREFIX} {request_id}",
                    },
                }
            ],
        ),
        ToolMessage(content="waiting_for_user_approval", tool_call_id=tool_call_id),
    ]


def _approved_question(approval_token: str, messages: Sequence[AnyMessage]) -> str | None:
    return pending_data_approvals.pop(approval_token, None) or _previous_unapproved_user_message(messages)


def _render_component_messages(question: str, response: FoundryAgentResponse, app_settings: Settings) -> list[AnyMessage]:
    messages: list[AnyMessage] = []
    calls = build_component_calls(question, response.answer, app_settings.databricks_sql_warehouse_name)
    for call in calls:
        tool_call_id = f"{call.name}-{uuid.uuid4().hex[:8]}"
        messages.append(AIMessage(content="", tool_calls=[{"id": tool_call_id, "name": call.name, "args": call.args}]))
        messages.append(ToolMessage(content="rendered", tool_call_id=tool_call_id))
    return messages


def _safe_error_message(prefix: str, exc: Exception) -> AIMessage:
    return AIMessage(content=f"{prefix} Safe technical detail: {type(exc).__name__}: {exc}")


async def _emit_progress(message: str) -> None:
    with suppress(RuntimeError):
        await adispatch_custom_event(
            "manually_emit_message",
            {"message_id": f"progress-{uuid.uuid4().hex[:8]}", "message": message},
        )


async def supervise_request(state: AgentState) -> dict[str, Any]:
    messages = state.get("messages", [])
    question = _last_user_message(messages)
    if not question:
        return {"route": "direct"}
    if _approval_token(question):
        return {"route": "risk_data"}

    decision: RouteDecision = await asyncio.to_thread(
        foundry_client.supervise,
        messages,
        bool(_conversation_id(state)),
    )
    return {"route": decision.route}


def route_supervisor_decision(state: AgentState) -> GraphNode:
    return "run_risk" if state.get("route") == "risk_data" else "direct_response"


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
    await _emit_progress("Approval received. Continuing the Azure AI Foundry conversation…")
    await _emit_progress("Foundry will use its active conversation and call Genie only if new governed data is required.")

    messages: list[AnyMessage] = [AIMessage(content="Query authorized. I have prepared the governed data analysis flow.")]
    try:
        response = await asyncio.to_thread(foundry_client.ask, question, conversation_id)
        messages.extend(_render_component_messages(question, response, settings))
        messages.append(AIMessage(content="I used the real Genie result through the active Foundry conversation to compose the view."))
        conversation_id = response.conversation_id or conversation_id
    except Exception as exc:
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

    approval_token = _approval_token(question)
    if approval_token:
        question = _approved_question(approval_token, input_messages) or ""
        if not question:
            return _state_update(
                [AIMessage(content="I cannot find that approval request. Run the query again to generate a valid authorization.")],
                conversation_id,
            )
    elif settings.require_human_data_approval:
        return _state_update(_approval_request(question), conversation_id)

    return await _execute_risk_query(question, conversation_id)


def build_agent_graph() -> Any:
    graph_builder = StateGraph(AgentState)
    graph_builder.add_node(NODE_SUPERVISE, supervise_request)
    graph_builder.add_node(NODE_DIRECT, direct_response)
    graph_builder.add_node(NODE_RISK, run_risk)
    graph_builder.add_edge(START, NODE_SUPERVISE)
    graph_builder.add_conditional_edges(
        NODE_SUPERVISE,
        route_supervisor_decision,
        {NODE_DIRECT: NODE_DIRECT, NODE_RISK: NODE_RISK},
    )
    graph_builder.add_edge(NODE_DIRECT, END)
    graph_builder.add_edge(NODE_RISK, END)
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
