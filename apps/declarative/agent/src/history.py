"""Message-history utilities shared by the LLM-facing nodes."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage


def content_text(content: Any) -> str:
    """Flatten message content that may arrive as a list of text blocks (reasoning models)."""
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


def last_user_message(messages: list[AnyMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage) or getattr(message, "type", None) == "human":
            return content_text(message.content)
    return ""


def repair_orphan_tool_calls(messages: list[AnyMessage]) -> list[AnyMessage]:
    """Insert synthetic results for tool calls that never got one.

    The generative-UI middlewares render streamed tool calls client-side but do
    not always synthesize a TOOL_CALL_RESULT, so on the next turn the history
    carries a dangling tool call and OpenAI-style APIs reject it ("No tool
    output found for function call ...").
    """
    answered = {message.tool_call_id for message in messages if isinstance(message, ToolMessage)}
    repaired: list[AnyMessage] = []
    for message in messages:
        repaired.append(message)
        if isinstance(message, AIMessage):
            for call in message.tool_calls or []:
                if call.get("id") and call["id"] not in answered:
                    repaired.append(ToolMessage(content='{"status": "rendered"}', tool_call_id=call["id"]))
    return repaired
