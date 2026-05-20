from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

import main
from main import FOUNDRY_CONVERSATION_KEY, _approval_request, _approved_question, _previous_unapproved_user_message
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


def test_approval_request_registers_deterministic_command_payload() -> None:
    main.pending_data_approvals.clear()

    messages = _approval_request("Show exposure by country")

    assert isinstance(messages[1], AIMessage)
    tool_call = messages[1].tool_calls[0]
    request_id = tool_call["args"]["requestId"]
    assert tool_call["name"] == "mcpApprovalCard"
    assert tool_call["args"]["approvalCommand"] == f"approve {request_id}"
    assert tool_call["args"]["rejectCommand"] == f"reject {request_id}"
    assert tool_call["args"]["reviseCommandPrefix"] == f"revise {request_id}:"
    assert main.pending_data_approvals[request_id].question == "Show exposure by country"
    assert main.pending_data_approvals[request_id].status == "pending"


def _pending_approval(request_id: str = "abc123", question: str = "Show exposure by country") -> main.PendingApproval:
    now = datetime.now(timezone.utc)
    return main.PendingApproval(
        request_id=request_id,
        question=question,
        purpose="test",
        created_at=now,
        expires_at=now + timedelta(minutes=5),
        audit_id="approval-test",
    )


def test_approved_question_consumes_pending_request_once() -> None:
    main.pending_data_approvals.clear()
    main.pending_data_approvals["abc123"] = _pending_approval()

    assert _approved_question("abc123", []) == "Show exposure by country"
    assert main.pending_data_approvals["abc123"].status == "used"
    assert _approved_question("abc123", []) is None


def test_approved_question_falls_back_to_previous_user_message_for_legacy_sessions() -> None:
    messages = [
        HumanMessage(content="Show overdue balance by risk class", id="question"),
        HumanMessage(content="approve missing", id="approval"),
    ]

    assert _approved_question("missing", messages) == "Show overdue balance by risk class"


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


async def test_supervisor_routes_simple_greeting_without_foundry_json(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_supervise(messages: list[Any], has_foundry_conversation: bool = False) -> RouteDecision:
        raise AssertionError("Simple greetings should not call the JSON-routing supervisor")

    monkeypatch.setattr(main.foundry_client, "supervise", fail_supervise)

    result = await main.supervise_request({"messages": [HumanMessage(content="Hi!")]})

    assert result["route"] == "direct"


async def test_risk_data_node_still_requires_approval() -> None:
    result = await main.run_risk({"messages": [HumanMessage(content="Show the top 5 brokers by claim amount")], "route": "risk_data"})

    messages = result["messages"]
    assert messages[0].content == "Approval required before querying governed data."
    assert messages[1].tool_calls[0]["name"] == "mcpApprovalCard"


async def test_rejected_approval_does_not_query_genie(monkeypatch: pytest.MonkeyPatch) -> None:
    main.pending_data_approvals.clear()
    main.pending_data_approvals["abc123"] = _pending_approval()

    async def fail_query(question: str, conversation_id: str | None, approval_request_id: str | None = None) -> dict[str, Any]:
        raise AssertionError("Genie must not be queried after rejection")

    monkeypatch.setattr(main, "_execute_risk_query", fail_query)

    result = await main.run_risk({"messages": [HumanMessage(content="reject abc123")], "route": "risk_data"})

    assert result["messages"][0].content == "Data access request rejected. I did not query Genie."
    assert main.pending_data_approvals["abc123"].status == "rejected"


async def test_revised_approval_uses_revised_question(monkeypatch: pytest.MonkeyPatch) -> None:
    main.pending_data_approvals.clear()
    main.pending_data_approvals["abc123"] = _pending_approval(question="Show exposure by country")
    queried: list[str] = []

    async def capture_query(question: str, conversation_id: str | None, approval_request_id: str | None = None) -> dict[str, Any]:
        queried.append(question)
        assert approval_request_id == "abc123"
        return {"messages": [AIMessage(content="ok")]}

    monkeypatch.setattr(main, "_execute_risk_query", capture_query)

    result = await main.run_risk({"messages": [HumanMessage(content="revise abc123: Show exposure by broker")], "route": "risk_data"})

    assert result["messages"][0].content == "ok"
    assert queried == ["Show exposure by broker"]
    assert main.pending_data_approvals["abc123"].status == "used"


async def test_expired_approval_does_not_query_genie(monkeypatch: pytest.MonkeyPatch) -> None:
    main.pending_data_approvals.clear()
    expired = _pending_approval()
    expired.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    main.pending_data_approvals["abc123"] = expired

    async def fail_query(question: str, conversation_id: str | None, approval_request_id: str | None = None) -> dict[str, Any]:
        raise AssertionError("Genie must not be queried after expiration")

    monkeypatch.setattr(main, "_execute_risk_query", fail_query)

    result = await main.run_risk({"messages": [HumanMessage(content="approve abc123")], "route": "risk_data"})

    assert "expired" in result["messages"][0].content
    assert main.pending_data_approvals["abc123"].status == "expired"


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
        "query.completed",
        "visualization.rendered",
    ]
    assert all(event["schemaVersion"] == "risk-ui/v1" for event in risk_events)
    assert all(
        not (hasattr(message, "tool_calls") and any(tc.get("name") == "agentStatusCard" for tc in (message.tool_calls or [])))
        for message in result["messages"]
    )
    assert result[FOUNDRY_CONVERSATION_KEY] == "conversation-2"
