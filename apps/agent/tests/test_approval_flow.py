from __future__ import annotations

from typing import Any

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

import main
from main import FOUNDRY_CONVERSATION_KEY, _previous_unapproved_user_message
from src.foundry_agent_client import FoundryAgentClient, FoundryAgentResponse, RouteDecision


def test_previous_unapproved_user_message_skips_approval_command() -> None:
    messages = [
        HumanMessage(content="Show the top 5 brokers by claim amount", id="question"),
        HumanMessage(content="approve abc123", id="approval"),
    ]

    assert _previous_unapproved_user_message(messages) == "Show the top 5 brokers by claim amount"


def test_previous_unapproved_user_message_returns_none_without_business_question() -> None:
    messages = [HumanMessage(content="approve abc123", id="approval")]

    assert _previous_unapproved_user_message(messages) is None


def test_route_decision_parser_accepts_json_with_markdown_fence() -> None:
    client = FoundryAgentClient(main.settings)

    decision = client._parse_route_decision('```json\n{"route":"direct","rationale":"No data needed"}\n```')

    assert decision == RouteDecision(route="direct", direct_answer=None, rationale="No data needed")


def test_route_decision_parser_rejects_unknown_route() -> None:
    client = FoundryAgentClient(main.settings)

    with pytest.raises(ValueError, match="Unsupported route"):
        client._parse_route_decision('{"route":"unknown","rationale":"bad"}')


class FakeAgentNode:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(state)
        return self.responses.pop(0)


def test_foundry_supervisor_uses_langgraph_agent_node(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FoundryAgentClient(main.settings)
    node = FakeAgentNode(
        [
            {
                "messages": AIMessage(content='{"route":"direct","rationale":"No data"}'),
                FOUNDRY_CONVERSATION_KEY: "ephemeral-supervisor-conversation",
            }
        ]
    )
    monkeypatch.setattr(client, "_foundry_agent_node", lambda: node)

    decision = client.supervise([HumanMessage(content="Hola")], has_foundry_conversation=True)

    assert decision == RouteDecision(route="direct", direct_answer=None, rationale="No data")
    assert isinstance(node.calls[0]["messages"][0], HumanMessage)
    assert "A Foundry conversation id is active" in node.calls[0]["messages"][0].content


def test_foundry_direct_answer_preserves_conversation_id(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FoundryAgentClient(main.settings)
    node = FakeAgentNode(
        [
            {
                "messages": AIMessage(content="Respuesta directa"),
                FOUNDRY_CONVERSATION_KEY: "conversation-2",
            }
        ]
    )
    monkeypatch.setattr(client, "_foundry_agent_node", lambda: node)

    response = client.answer_direct("Hola", conversation_id="conversation-1")

    assert response == FoundryAgentResponse(answer="Respuesta directa", conversation_id="conversation-2")
    assert node.calls[0][FOUNDRY_CONVERSATION_KEY] == "conversation-1"


def test_foundry_ask_completes_mcp_approval_through_langgraph_node(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FoundryAgentClient(main.settings)
    node = FakeAgentNode(
        [
            {
                "messages": AIMessage(content="", tool_calls=[{"id": "approval-1", "name": "mcp_approval_request", "args": {}}]),
                FOUNDRY_CONVERSATION_KEY: "conversation-1",
                "azure_ai_agents_previous_response_id": "response-1",
                "azure_ai_agents_pending_type": "mcp_approval",
            },
            {
                "messages": AIMessage(content="Data-backed answer"),
                FOUNDRY_CONVERSATION_KEY: "conversation-1",
                "azure_ai_agents_previous_response_id": "response-2",
                "azure_ai_agents_pending_type": None,
            },
        ]
    )
    monkeypatch.setattr(client, "_foundry_agent_node", lambda: node)

    response = client.ask("Show top brokers")

    assert response.answer == "Data-backed answer"
    assert response.conversation_id == "conversation-1"
    assert isinstance(node.calls[1]["messages"][0], ToolMessage)
    assert node.calls[1]["azure_ai_agents_pending_type"] == "mcp_approval"


async def test_supervisor_uses_foundry_decision_for_general_question(monkeypatch: pytest.MonkeyPatch) -> None:
    def supervise(messages: list[Any], has_foundry_conversation: bool = False) -> RouteDecision:
        assert messages[-1].content == "Hola, ¿qué puedes hacer?"
        assert has_foundry_conversation is False
        return RouteDecision(route="direct", direct_answer=None, rationale="No governed data needed.")

    monkeypatch.setattr(main.foundry_client, "supervise", supervise)

    result = await main.supervise_request({"messages": [HumanMessage(content="Hola, ¿qué puedes hacer?")]})

    assert result["route"] == "direct"


async def test_direct_response_uses_foundry_conversation(monkeypatch: pytest.MonkeyPatch) -> None:
    def answer_direct(question: str, conversation_id: str | None = None) -> FoundryAgentResponse:
        assert question == "Hola"
        assert conversation_id == "conversation-1"
        return FoundryAgentResponse(answer="Hola desde Foundry", conversation_id="conversation-2")

    monkeypatch.setattr(main.foundry_client, "answer_direct", answer_direct)

    result = await main.direct_response({"messages": [HumanMessage(content="Hola")], "azure_ai_agents_conversation_id": "conversation-1"})

    assert result["messages"][0].content == "Hola desde Foundry"
    assert result[FOUNDRY_CONVERSATION_KEY] == "conversation-2"


async def test_supervisor_routes_concrete_risk_question_to_genie(monkeypatch: pytest.MonkeyPatch) -> None:
    def supervise(messages: list[Any], has_foundry_conversation: bool = False) -> RouteDecision:
        assert messages[-1].content == "Show the top 5 brokers by claim amount"
        return RouteDecision(route="risk_data", direct_answer=None, rationale="Requires governed aggregation.")

    monkeypatch.setattr(main.foundry_client, "supervise", supervise)

    result = await main.supervise_request({"messages": [HumanMessage(content="Show the top 5 brokers by claim amount")]})

    assert result["route"] == "risk_data"


async def test_risk_data_node_still_requires_approval() -> None:
    result = await main.run_risk({"messages": [HumanMessage(content="Show the top 5 brokers by claim amount")], "route": "risk_data"})

    messages = result["messages"]
    assert messages[0].content == "Approval required before querying governed data."
    assert messages[1].tool_calls[0]["name"] == "mcpApprovalCard"
