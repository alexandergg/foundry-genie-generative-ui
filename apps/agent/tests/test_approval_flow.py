from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

import main
from main import (
    FOUNDRY_CONVERSATION_KEY,
    ApprovalCommand,
    _approval_request,
    _resolve_approved_question,
)
from src.foundry_agent_client import FoundryAgentClient, FoundryAgentResponse, RouteDecision


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


def test_approval_request_purges_resolved_and_stale_pending_entries() -> None:
    main.pending_data_approvals.clear()
    now = datetime.now(timezone.utc)

    used = _pending_approval(request_id="used1")
    used.status = "used"
    main.pending_data_approvals["used1"] = used

    rejected = _pending_approval(request_id="rejected1")
    rejected.status = "rejected"
    main.pending_data_approvals["rejected1"] = rejected

    leaked_pending = _pending_approval(request_id="leaked1")
    leaked_pending.created_at = now - timedelta(minutes=2 * main.APPROVAL_TTL_MINUTES + 1)
    main.pending_data_approvals["leaked1"] = leaked_pending

    fresh = _pending_approval(request_id="fresh1")
    fresh.created_at = now
    main.pending_data_approvals["fresh1"] = fresh

    messages = _approval_request("Show exposure by country")
    assert isinstance(messages[1], AIMessage)
    new_request_id = messages[1].tool_calls[0]["args"]["requestId"]

    assert "used1" not in main.pending_data_approvals
    assert "rejected1" not in main.pending_data_approvals
    assert "leaked1" not in main.pending_data_approvals
    assert "fresh1" in main.pending_data_approvals
    assert new_request_id in main.pending_data_approvals
    assert set(main.pending_data_approvals) == {"fresh1", new_request_id}


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


def _approve(request_id: str) -> str | None:
    return _resolve_approved_question(ApprovalCommand(action="approve", request_id=request_id))


def test_approved_question_consumes_pending_request_once() -> None:
    main.pending_data_approvals.clear()
    main.pending_data_approvals["abc123"] = _pending_approval()

    assert _approve("abc123") == "Show exposure by country"
    assert main.pending_data_approvals["abc123"].status == "used"
    assert _approve("abc123") is None


def test_unknown_approval_id_is_rejected_strictly() -> None:
    # A governed query may only be authorized by a real, recorded approval; an
    # unknown id (typo, fabricated, or a lost in-memory store) never falls back
    # to the last user message.
    main.pending_data_approvals.clear()

    assert _approve("missing") is None


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


async def test_unknown_approval_does_not_query_genie(monkeypatch: pytest.MonkeyPatch) -> None:
    main.pending_data_approvals.clear()

    async def fail_query(question: str, conversation_id: str | None, approval_request_id: str | None = None) -> dict[str, Any]:
        raise AssertionError("Genie must not be queried for an unknown approval id")

    monkeypatch.setattr(main, "_execute_risk_query", fail_query)

    result = await main.run_risk({"messages": [HumanMessage(content="approve ghost123")], "route": "risk_data"})

    assert "cannot use that approval request" in result["messages"][0].content


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


async def test_run_risk_emits_approval_requested_when_approval_required(monkeypatch: pytest.MonkeyPatch) -> None:
    main.pending_data_approvals.clear()
    emitted: list[dict[str, Any]] = []

    async def capture_event(name: str, payload: dict[str, Any]) -> None:
        if name == "risk_ui_event":
            emitted.append(payload)

    monkeypatch.setattr(main, "adispatch_custom_event", capture_event)
    assert main.settings.require_human_data_approval, "test env must require approval"

    await main.run_risk({"messages": [HumanMessage(content="Show exposure by country")], "route": "risk_data"})

    approval_events = [event for event in emitted if event["kind"] == "approval.requested"]
    assert len(approval_events) == 1
    assert approval_events[0]["phase"] == "approval"


async def test_run_risk_emits_approval_updated_on_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    main.pending_data_approvals.clear()
    main.pending_data_approvals["abc123"] = _pending_approval()
    emitted: list[dict[str, Any]] = []

    async def capture_event(name: str, payload: dict[str, Any]) -> None:
        if name == "risk_ui_event":
            emitted.append(payload)

    async def stub_query(question: str, conversation_id: str | None, approval_request_id: str | None = None) -> dict[str, Any]:
        return {"messages": [AIMessage(content="ok")]}

    monkeypatch.setattr(main, "adispatch_custom_event", capture_event)
    monkeypatch.setattr(main, "_execute_risk_query", stub_query)

    await main.run_risk({"messages": [HumanMessage(content="approve abc123")], "route": "risk_data"})

    approval_events = [event for event in emitted if event["kind"] == "approval.updated"]
    assert len(approval_events) == 1
    assert approval_events[0]["payload"]["status"] == "approved"


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
