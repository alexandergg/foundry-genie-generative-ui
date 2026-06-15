from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, SystemMessage, ToolMessage

from src import graph as graph_module
from src.graph import MISSING_TOOLS_MESSAGE, SANDBOXED_UI_TOOL_NAME, AgentState, agent_graph, generate_ui

SANDBOXED_UI_TOOL = {
    "name": SANDBOXED_UI_TOOL_NAME,
    "description": "Generate sandboxed UI.",
    "parameters": {"type": "object", "properties": {"html": {"type": "string"}}},
}

EXCALIDRAW_TOOL = {
    "name": "excalidraw_create_scene",
    "description": "Create an Excalidraw whiteboard scene.",
    "parameters": {"type": "object", "properties": {"prompt": {"type": "string"}}},
}


class FakeChatModel:
    """Streams one tool-call chunk, mirroring the contract generate_ui relies on."""

    def __init__(self) -> None:
        self.bound_tools: list[Any] = []
        self.received_messages: list[Any] = []

    def bind_tools(self, tools: list[Any]) -> FakeChatModel:
        self.bound_tools = tools
        return self

    async def astream(self, messages: list[Any]) -> AsyncIterator[AIMessageChunk]:
        self.received_messages = messages
        yield AIMessageChunk(
            content="",
            tool_call_chunks=[
                {"id": "call-1", "name": SANDBOXED_UI_TOOL_NAME, "args": '{"html": "<div>hi</div>"}', "index": 0, "type": "tool_call_chunk"}
            ],
        )


async def test_generate_ui_binds_all_injected_tools_and_grounds_prompt(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    fake = FakeChatModel()
    monkeypatch.setattr(graph_module, "get_chat_model", lambda: fake)

    state: AgentState = {
        "messages": [HumanMessage(content="Build me a widget")],
        "ag-ui": {
            "tools": [SANDBOXED_UI_TOOL, EXCALIDRAW_TOOL],
            "context": [{"description": "User timezone", "value": "Europe/Madrid"}],
        },
    }
    result = await generate_ui(state)

    assert [tool["name"] for tool in fake.bound_tools] == [SANDBOXED_UI_TOOL_NAME, "excalidraw_create_scene"]
    system = fake.received_messages[0]
    assert isinstance(system, SystemMessage)
    assert "Spain" in str(system.content)  # domain grounding from the sample dataset
    assert "generateSandboxedUi" in str(system.content)  # tool guidance
    assert "Europe/Madrid" in str(system.content)  # forwarded context

    response = result["messages"][0]
    assert isinstance(response, AIMessage)
    assert response.tool_calls[0]["name"] == SANDBOXED_UI_TOOL_NAME


async def test_generate_ui_degrades_when_no_tools_are_injected() -> None:
    result = await generate_ui({"messages": [HumanMessage(content="hi")]})
    assert result["messages"][0].content == MISSING_TOOLS_MESSAGE


async def test_generate_ui_repairs_orphan_tool_calls_in_history(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    fake = FakeChatModel()
    monkeypatch.setattr(graph_module, "get_chat_model", lambda: fake)

    # Previous turn ended on a tool call the middleware rendered client-side
    # but never answered — without repair, OpenAI-style APIs reject the history.
    state: AgentState = {
        "messages": [
            HumanMessage(content="Build me a widget"),
            AIMessage(content="", tool_calls=[{"id": "call-old", "name": SANDBOXED_UI_TOOL_NAME, "args": {}}]),
            HumanMessage(content="Now make it more compact"),
        ],
        "ag-ui": {"tools": [SANDBOXED_UI_TOOL]},
    }
    await generate_ui(state)

    sent = fake.received_messages
    orphan_index = next(i for i, m in enumerate(sent) if isinstance(m, AIMessage) and m.tool_calls)
    follow_up = sent[orphan_index + 1]
    assert isinstance(follow_up, ToolMessage)
    assert follow_up.tool_call_id == "call-old"


async def test_graph_accepts_the_hyphenated_ag_ui_channel(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    fake = FakeChatModel()
    monkeypatch.setattr(graph_module, "get_chat_model", lambda: fake)

    result = await agent_graph.ainvoke(
        {
            "messages": [HumanMessage(content="Build me a widget")],
            "ag-ui": {"tools": [SANDBOXED_UI_TOOL]},
        },
        config={"configurable": {"thread_id": "test-thread"}},
    )
    final = result["messages"][-1]
    assert isinstance(final, AIMessage)
    assert final.tool_calls and final.tool_calls[0]["name"] == SANDBOXED_UI_TOOL_NAME


async def test_generate_ui_reports_model_failures_safely(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def boom() -> None:
        raise RuntimeError("endpoint not configured")

    monkeypatch.setattr(graph_module, "get_chat_model", boom)
    failing_state: AgentState = {
        "messages": [HumanMessage(content="Build")],
        "ag-ui": {"tools": [SANDBOXED_UI_TOOL]},
    }
    result = await generate_ui(failing_state)
    assert "Foundry model" in str(result["messages"][0].content)
