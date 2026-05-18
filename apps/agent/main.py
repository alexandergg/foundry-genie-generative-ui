from __future__ import annotations

import asyncio
import os
import uuid
import warnings
from typing import Annotated, Any, TypedDict

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
from src.foundry_agent_client import FoundryAgentClient
from src.session_context import build_context_snapshot, cached_context_answer
from src.visualization_mapper import build_component_calls

load_dotenv()
settings = load_settings()
foundry_client = FoundryAgentClient(settings)
pending_data_approvals: dict[str, str] = {}
APPROVAL_COMMAND_PREFIX = "approve"


class AgentState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    session_context: dict[str, Any] | None


def _last_user_message(messages: list[AnyMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage) or getattr(message, "type", None) == "human":
            content = message.content
            return content if isinstance(content, str) else str(content)
    return ""


def _approval_token(message: str) -> str | None:
    if not message.startswith(APPROVAL_COMMAND_PREFIX):
        return None
    token = message.removeprefix(APPROVAL_COMMAND_PREFIX).strip().strip(".")
    return token or None


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
                        "dataSource": "Databricks Genie Space UC3 through Azure AI Foundry MCP",
                        "purpose": "Send the question to the Foundry agent to query exposure, claims, brokers or overdue balances.",
                        "approvalCommand": f"{APPROVAL_COMMAND_PREFIX} {request_id}",
                    },
                }
            ],
        ),
        ToolMessage(content="waiting_for_user_approval", tool_call_id=tool_call_id),
    ]


async def _emit_progress(message: str) -> None:
    try:
        await adispatch_custom_event(
            "manually_emit_message",
            {"message_id": f"progress-{uuid.uuid4().hex[:8]}", "message": message},
        )
    except RuntimeError:
        pass


async def run_uc3(state: AgentState) -> dict[str, Any]:
    question = _last_user_message(state.get("messages", []))
    if not question:
        return {"messages": [AIMessage(content="What would you like to analyze about exposure, claims, brokers or overdue balances?")]}

    approval_token = _approval_token(question)
    if approval_token:
        approved_question = pending_data_approvals.pop(approval_token, None)
        if not approved_question:
            return {"messages": [AIMessage(content="I cannot find that approval request. Run the query again to generate a valid authorization.")]}
        question = approved_question
    else:
        cached = cached_context_answer(question, state.get("session_context"), settings.databricks_sql_warehouse_name)
        if cached:
            cached_answer, cached_calls = cached
            messages: list[AnyMessage] = [AIMessage(content=cached_answer)]
            for call in cached_calls:
                tool_call_id = f"{call.name}-{uuid.uuid4().hex[:8]}"
                messages.append(AIMessage(content="", tool_calls=[{"id": tool_call_id, "name": call.name, "args": call.args}]))
                messages.append(ToolMessage(content="rendered_from_session_cache", tool_call_id=tool_call_id))
            return {"messages": messages, "session_context": state.get("session_context")}
        if settings.require_human_data_approval:
            return {"messages": _approval_request(question), "session_context": state.get("session_context")}

    await _emit_progress("Approval received. Continuing the Azure AI Foundry conversation…")
    await _emit_progress("Foundry will reuse prior Genie context when sufficient, or query Genie only when new governed data is needed.")

    messages: list[AnyMessage] = [
        AIMessage(content="Query authorized. I have prepared the governed data analysis flow."),
    ]

    session_context = dict(state.get("session_context") or {})
    foundry_conversation_id = session_context.get("foundry_conversation_id")

    try:
        response = await asyncio.to_thread(foundry_client.ask, question, foundry_conversation_id)
        calls = build_component_calls(question, response.answer, settings.databricks_sql_warehouse_name)
        for call in calls:
            tool_call_id = f"{call.name}-{uuid.uuid4().hex[:8]}"
            messages.append(AIMessage(content="", tool_calls=[{"id": tool_call_id, "name": call.name, "args": call.args}]))
            messages.append(ToolMessage(content="rendered", tool_call_id=tool_call_id))

        session_context.update(
            {
                "foundry_conversation_id": response.conversation_id,
                "last_question": question,
                "last_answer": response.answer[:4000],
            }
        )
        table_context = build_context_snapshot(question, response.answer)
        if table_context:
            session_context.update(table_context)

        memory_note = " The same Foundry conversation is now active for follow-up questions."
        messages.append(AIMessage(content=f"I used the real Genie result to compose the view.{memory_note}"))
    except Exception as exc:
        messages.append(
            AIMessage(
                content=(
                    "I could not complete the real query against Foundry/Genie. "
                    "Check Azure CLI authentication, Databricks permissions and SQL Warehouse availability. "
                    f"Safe technical detail: {type(exc).__name__}: {exc}"
                )
            )
        )

    return {"messages": messages, "session_context": session_context}


graph_builder = StateGraph(AgentState)
graph_builder.add_node("run_uc3", run_uc3)
graph_builder.add_edge(START, "run_uc3")
graph_builder.add_edge("run_uc3", END)
agent_graph = graph_builder.compile(checkpointer=InMemorySaver())

app = FastAPI(title="UC3 Generative UI Agent")


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
    agent=LangGraphAGUIAgent(
        name="default",
        description="UC3 Foundry/Genie Generative UI agent",
        graph=agent_graph,
    ),
    path="/",
)

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8123")), reload=True)
