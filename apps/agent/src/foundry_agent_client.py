from __future__ import annotations

import json
import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol, cast

from langchain_core.messages import AIMessage, AnyMessage, BaseMessage, HumanMessage, ToolMessage

from .config import Settings

CONVERSATION_ID_KEY = "azure_ai_agents_conversation_id"
PREVIOUS_RESPONSE_ID_KEY = "azure_ai_agents_previous_response_id"
PENDING_TYPE_KEY = "azure_ai_agents_pending_type"
MCP_APPROVAL_PENDING = "mcp_approval"

Route = Literal["direct", "risk_data"]
FoundryAgentState = dict[str, Any]

_TRANSCRIPT_MESSAGE_LIMIT = 8
_TRANSCRIPT_TEXT_LIMIT = 1_200


class LangGraphAgentNode(Protocol):
    def invoke(self, state: FoundryAgentState) -> FoundryAgentState: ...


@dataclass(frozen=True)
class FoundryAgentResponse:
    answer: str
    conversation_id: str | None = None


@dataclass(frozen=True)
class RouteDecision:
    route: Route
    direct_answer: str | None
    rationale: str


class FoundryAgentClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._agent_node_cache: LangGraphAgentNode | None = None

    def _configured_agent_version(self) -> str | None:
        version = self.settings.agent_version
        if not version:
            return None
        if version.startswith(f"{self.settings.agent_name}:"):
            return version.split(":", 1)[1]
        return version

    def _foundry_agent_node(self) -> LangGraphAgentNode:
        if self._agent_node_cache is not None:
            return self._agent_node_cache
        if not self.settings.project_endpoint:
            raise RuntimeError(
                "RISK_GENIE_PROJECT_ENDPOINT or FOUNDRY_PROJECT_ENDPOINT is not configured and .foundry metadata was not found."
            )
        if not self.settings.agent_name:
            raise RuntimeError("RISK_GENIE_AGENT_NAME or FOUNDRY_AGENT_NAME is not configured.")

        try:
            from azure.identity import DefaultAzureCredential
            from langchain_azure_ai.agents import AgentServiceFactory
        except ImportError as exc:
            raise RuntimeError("Azure Foundry LangGraph dependencies are missing. Run `pip install -e apps/agent`.") from exc

        factory = AgentServiceFactory(project_endpoint=self.settings.project_endpoint, credential=DefaultAzureCredential())
        self._agent_node_cache = cast(
            LangGraphAgentNode,
            factory.get_agent_node(
                name=self.settings.agent_name,
                version=self._configured_agent_version(),
                trace=False,
            ),
        )
        return self._agent_node_cache

    @staticmethod
    def _conversation_id(state: FoundryAgentState) -> str | None:
        value = state.get(CONVERSATION_ID_KEY)
        return value if isinstance(value, str) else None

    @staticmethod
    def _pending_type(state: FoundryAgentState) -> str | None:
        value = state.get(PENDING_TYPE_KEY)
        return value if isinstance(value, str) else None

    @staticmethod
    def _agent_state(message: AnyMessage, conversation_id: str | None = None) -> FoundryAgentState:
        state: FoundryAgentState = {"messages": [message]}
        if conversation_id:
            state[CONVERSATION_ID_KEY] = conversation_id
        return state

    @staticmethod
    def _message_text(message: AnyMessage) -> str:
        content = message.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            fragments: list[str] = []
            for item in content:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    fragments.append(item["text"])
                elif isinstance(item, str):
                    fragments.append(item)
            return "\n".join(fragments)
        return str(content)

    @staticmethod
    def _messages_from_state(state: FoundryAgentState) -> list[AnyMessage]:
        messages = state.get("messages", [])
        if isinstance(messages, list):
            return cast(list[AnyMessage], messages)
        if isinstance(messages, BaseMessage):
            return [cast(AnyMessage, messages)]
        return []

    def _last_ai_message(self, state: FoundryAgentState) -> AIMessage | None:
        for message in reversed(self._messages_from_state(state)):
            if isinstance(message, AIMessage) or getattr(message, "type", None) == "ai":
                return cast(AIMessage, message)
        return None

    def _approval_tool_call_id(self, state: FoundryAgentState) -> str | None:
        message = self._last_ai_message(state)
        if message is None:
            return None
        for tool_call in message.tool_calls:
            call_id = tool_call.get("id")
            if isinstance(call_id, str):
                return call_id
        return None

    def _invoke_agent_node(self, message: AnyMessage, conversation_id: str | None = None) -> FoundryAgentState:
        return self._foundry_agent_node().invoke(self._agent_state(message, conversation_id))

    def _approval_continuation_state(self, state: FoundryAgentState, tool_call_id: str) -> FoundryAgentState:
        return {
            "messages": [ToolMessage(content=json.dumps({"approve": True}), tool_call_id=tool_call_id)],
            CONVERSATION_ID_KEY: self._conversation_id(state),
            PREVIOUS_RESPONSE_ID_KEY: state.get(PREVIOUS_RESPONSE_ID_KEY),
            PENDING_TYPE_KEY: self._pending_type(state),
        }

    def _complete_langgraph_mcp_approvals(self, state: FoundryAgentState) -> FoundryAgentState:
        node = self._foundry_agent_node()
        current_state = state
        for _ in range(self.settings.mcp_approval_rounds):
            if self._pending_type(current_state) != MCP_APPROVAL_PENDING:
                return current_state
            tool_call_id = self._approval_tool_call_id(current_state)
            if not tool_call_id:
                raise RuntimeError("Foundry requested MCP approval but did not return an approval tool call id.")
            current_state = node.invoke(self._approval_continuation_state(current_state, tool_call_id))
        if self._pending_type(current_state) == MCP_APPROVAL_PENDING:
            raise RuntimeError(f"Foundry/Genie kept requesting MCP approvals after {self.settings.mcp_approval_rounds} rounds.")
        return current_state

    @staticmethod
    def _looks_transient(answer: str) -> bool:
        lowered = answer.lower()
        transient_markers = (
            "in progress",
            "still running",
            "continues running",
            "en proceso",
            "está en proceso",
            "continúa en ejecución",
            "sigue ejecut",
            "puede deberse",
        )
        warehouse_markers = ("warehouse", "sql warehouse", "stopped", "start", "warming", "parado", "arrancado")
        return any(marker in lowered for marker in transient_markers) and any(marker in lowered for marker in warehouse_markers)

    def _conversation_transcript(self, messages: Sequence[AnyMessage]) -> str:
        lines: list[str] = []
        for message in messages[-_TRANSCRIPT_MESSAGE_LIMIT:]:
            if isinstance(message, ToolMessage) or getattr(message, "type", None) == "tool":
                continue
            role = "user" if isinstance(message, HumanMessage) or getattr(message, "type", None) == "human" else "assistant"
            text = self._message_text(message).strip()
            if text:
                lines.append(f"{role}: {text[:_TRANSCRIPT_TEXT_LIMIT]}")
        return "\n".join(lines)

    def _route_supervisor_prompt(self, messages: Sequence[AnyMessage], has_foundry_conversation: bool) -> str:
        context_note = (
            "A Foundry conversation id is active, so the referenced Foundry agent already has prior turns and Genie tool results. "
            if has_foundry_conversation
            else "No Foundry conversation id is active yet. "
        )
        return (
            "You are the routing supervisor for a LangGraph hosted agent. Decide the next node using the full conversation, "
            "the user's latest intent, and whether existing Foundry conversation context can answer the request. "
            "Return only a valid JSON object with keys: route, rationale. route must be one of: direct, risk_data. "
            "Use route=risk_data only when the latest user request needs governed Databricks Genie data: retrieving, calculating, "
            "filtering, comparing, ranking, aggregating, or visualizing risk exposure, claims, brokers, overdue balances, countries, "
            "quarters, risk classes, or a follow-up that needs new governed data. Use route=direct when the answer can be produced "
            "from normal conversation context, Foundry conversation context, previous Genie results already in the conversation, or general knowledge. "
            "Never call tools while making this routing decision. "
            f"{context_note}Conversation:\n{self._conversation_transcript(messages)}"
        )

    @staticmethod
    def _json_object_from_text(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end >= start:
            cleaned = cleaned[start : end + 1]
        payload = json.loads(cleaned)
        if not isinstance(payload, dict):
            raise ValueError("Expected a JSON object from Foundry supervisor.")
        return cast(dict[str, Any], payload)

    def _parse_route_decision(self, text: str) -> RouteDecision:
        payload = self._json_object_from_text(text)
        route = payload.get("route")
        if route not in {"direct", "risk_data"}:
            raise ValueError(f"Unsupported route: {route}")
        direct_answer = payload.get("direct_answer")
        return RouteDecision(
            route=cast(Route, route),
            direct_answer=direct_answer if isinstance(direct_answer, str) else None,
            rationale=str(payload.get("rationale") or "No rationale returned."),
        )

    @staticmethod
    def _direct_prompt(question: str) -> str:
        return (
            "You are Genie Risk Copilot answering inside a Foundry hosted agent conversation. "
            "Answer the latest user message directly in the user's language. Use the existing Foundry conversation history, "
            "including any prior Databricks Genie results already present in this conversation, when it helps. "
            "Do not call Databricks Genie or any governed data tool for this direct response. If the request actually needs new governed data, "
            "say that it requires approval instead of querying. Keep the answer concise and helpful. "
            f"Latest user message: {question}"
        )

    @staticmethod
    def _genie_business_prompt(question: str, has_conversation_context: bool = False) -> str:
        context_instruction = (
            "Use the active Foundry conversation history, including prior Genie tool results, when they are sufficient. "
            "Only call Databricks Genie again when the user asks for new governed data, new filters, missing columns or a fresh calculation. "
            if has_conversation_context
            else "This is the first governed business query in this Foundry conversation. "
        )
        return (
            f"{context_instruction}"
            "You are the governed risk-data specialist behind a hosted AG-UI orchestrator. "
            "Call Databricks Genie only for concrete risk analytics requests that require data from the demo dataset, such as exposure, claims, brokers, overdue balances, countries, quarters or risk classes. "
            "If the user asks a greeting, app-help, conceptual, setup or non-risk question, answer directly without calling Genie. "
            "If you do call Databricks Genie, start a new Genie query/conversation; do not reuse Databricks Genie conversation_id values or IDs such as 1. "
            "Prefer the vw_risk_genie_exposure_claims view and answer in the same language as the user. "
            "When aggregated metrics are available, return a markdown table with stable columns and numeric values; never invent risk metrics or fill missing values from assumptions. "
            f"User question: {question}"
        )

    @staticmethod
    def _warehouse_retry_prompt() -> str:
        return (
            "The SQL Warehouse is already active. Continue the original query, "
            "keep polling Genie if needed and return the final data-backed result. "
            "Do not answer that the warehouse is stopped unless the technical error explicitly confirms it."
        )

    def _response_from_state(self, state: FoundryAgentState, missing_message: str) -> FoundryAgentResponse:
        response = self._last_ai_message(state)
        if response is None:
            raise RuntimeError(missing_message)
        return FoundryAgentResponse(answer=self._message_text(response), conversation_id=self._conversation_id(state))

    def _invoke_genie_once(self, question: str, conversation_id: str | None) -> FoundryAgentState:
        prompt = self._genie_business_prompt(question, has_conversation_context=bool(conversation_id))
        state = self._invoke_agent_node(HumanMessage(content=prompt), conversation_id)
        return self._complete_langgraph_mcp_approvals(state)

    def _resolve_transient_genie_response(self, state: FoundryAgentState) -> FoundryAgentResponse:
        response = self._response_from_state(state, "Foundry/Genie did not return an AI message.")
        for _ in range(self.settings.transient_response_retries):
            if not self._looks_transient(response.answer):
                return response
            time.sleep(3)
            state = self._invoke_agent_node(HumanMessage(content=self._warehouse_retry_prompt()), response.conversation_id)
            state = self._complete_langgraph_mcp_approvals(state)
            response = self._response_from_state(state, "Foundry/Genie did not return an AI message after retry.")
        return response

    def supervise(self, messages: Sequence[AnyMessage], has_foundry_conversation: bool = False) -> RouteDecision:
        response_state = self._invoke_agent_node(HumanMessage(content=self._route_supervisor_prompt(messages, has_foundry_conversation)))
        if self._pending_type(response_state) == MCP_APPROVAL_PENDING:
            return RouteDecision(route="risk_data", direct_answer=None, rationale="Supervisor attempted a governed tool call.")
        response = self._response_from_state(response_state, "Foundry supervisor did not return an AI message.")
        return self._parse_route_decision(response.answer)

    def answer_direct(self, question: str, conversation_id: str | None = None) -> FoundryAgentResponse:
        state = self._invoke_agent_node(HumanMessage(content=self._direct_prompt(question)), conversation_id)
        if self._pending_type(state) == MCP_APPROVAL_PENDING:
            raise RuntimeError("Direct response attempted to access governed data without approval.")
        return self._response_from_state(state, "Foundry direct response did not return an AI message.")

    def ask(self, question: str, conversation_id: str | None = None) -> FoundryAgentResponse:
        attempts = [conversation_id, None] if conversation_id else [None]
        last_error: Exception | None = None
        for attempt_conversation_id in attempts:
            try:
                state = self._invoke_genie_once(question, attempt_conversation_id)
                return self._resolve_transient_genie_response(state)
            except Exception as exc:
                last_error = exc
                if attempt_conversation_id is None:
                    raise
        raise last_error or RuntimeError("Foundry/Genie query failed without returning an error.")
