from __future__ import annotations

from typing import Any

import pytest
from langchain_core.messages import AIMessage, HumanMessage

import main
from main import FOUNDRY_CONVERSATION_KEY
from src.foundry_agent_client import FoundryAgentClient, FoundryAgentResponse, RouteDecision


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


async def test_supervisor_routes_greeting_through_the_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    # Routing is fully LLM-driven: greetings are no longer short-circuited by a
    # heuristic, so the supervisor model decides the route for them too.
    seen: list[str] = []

    def supervise(messages: list[Any], has_foundry_conversation: bool = False) -> RouteDecision:
        seen.append(messages[-1].content)
        return RouteDecision(route="direct", direct_answer=None, rationale="Greeting, no governed data needed.")

    monkeypatch.setattr(main.foundry_client, "supervise", supervise)

    result = await main.supervise_request({"messages": [HumanMessage(content="Hi!")]})

    assert result["route"] == "direct"
    assert seen == ["Hi!"]


async def test_supervisor_falls_back_to_direct_when_supervise_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    # The supervisor is the graph entry node and calls a network LLM; a transient
    # failure must not crash the run — it falls back to a direct response.
    def boom(messages: list[Any], has_foundry_conversation: bool = False) -> RouteDecision:
        raise RuntimeError("Foundry unavailable")

    monkeypatch.setattr(main.foundry_client, "supervise", boom)

    result = await main.supervise_request({"messages": [HumanMessage(content="Hi!")]})

    assert result["route"] == "direct"


async def test_supervisor_emits_plan_created_when_routing_to_governed_data(monkeypatch: pytest.MonkeyPatch) -> None:
    emitted: list[dict[str, Any]] = []

    async def capture_event(name: str, payload: dict[str, Any]) -> None:
        if name == "risk_ui_event":
            emitted.append(payload)

    def supervise(messages: list[Any], has_foundry_conversation: bool = False) -> RouteDecision:
        return RouteDecision(route="risk_data", direct_answer=None, rationale="Requires governed aggregation.")

    monkeypatch.setattr(main, "adispatch_custom_event", capture_event)
    monkeypatch.setattr(main.foundry_client, "supervise", supervise)

    await main.supervise_request({"messages": [HumanMessage(content="Show exposure by country")]})

    kinds = [event["kind"] for event in emitted]
    assert "plan.created" in kinds
    plan_event = next(event for event in emitted if event["kind"] == "plan.created")
    assert plan_event["phase"] == "supervise"
    assert plan_event["payload"]["message"]


async def test_supervisor_does_not_emit_plan_created_for_direct_route(monkeypatch: pytest.MonkeyPatch) -> None:
    emitted: list[dict[str, Any]] = []

    async def capture_event(name: str, payload: dict[str, Any]) -> None:
        if name == "risk_ui_event":
            emitted.append(payload)

    def supervise(messages: list[Any], has_foundry_conversation: bool = False) -> RouteDecision:
        return RouteDecision(route="direct", direct_answer=None, rationale="No governed data needed.")

    monkeypatch.setattr(main, "adispatch_custom_event", capture_event)
    monkeypatch.setattr(main.foundry_client, "supervise", supervise)

    await main.supervise_request({"messages": [HumanMessage(content="What can you do?")]})

    assert "plan.created" not in [event["kind"] for event in emitted]


async def test_execute_risk_query_emits_versioned_ui_events(monkeypatch: pytest.MonkeyPatch) -> None:
    emitted_events: list[tuple[str, dict[str, Any]]] = []

    async def capture_event(name: str, payload: dict[str, Any]) -> None:
        emitted_events.append((name, payload))

    def ask(question: str, conversation_id: str | None = None) -> FoundryAgentResponse:
        assert question == "Show exposure by country"
        assert conversation_id == "conversation-1"
        return FoundryAgentResponse(answer="No rows returned", conversation_id="conversation-2")

    monkeypatch.setattr(main, "adispatch_custom_event", capture_event)
    monkeypatch.setattr(main.foundry_client, "ask", ask)

    result = await main._execute_risk_query("Show exposure by country", "conversation-1")

    risk_events = [payload for name, payload in emitted_events if name == "risk_ui_event"]
    assert [event["kind"] for event in risk_events] == [
        "query.started",
        "normalization.started",
        "normalization.completed",
        "query.completed",
        "visualization.proposed",
        "visualization.rendered",
        "followups.suggested",
        "provenance.attached",
    ]
    assert all(event["schemaVersion"] == "risk-ui/v1" for event in risk_events)
    provenance = next(event for event in risk_events if event["kind"] == "provenance.attached")
    assert provenance["payload"]["traceId"].startswith("risk-")
    assert all(
        not (hasattr(message, "tool_calls") and any(tc.get("name") == "agentStatusCard" for tc in (message.tool_calls or [])))
        for message in result["messages"]
    )
    assert result[FOUNDRY_CONVERSATION_KEY] == "conversation-2"
