from __future__ import annotations

from langchain_core.messages import HumanMessage

from main import _previous_unapproved_user_message


def test_previous_unapproved_user_message_skips_approval_command() -> None:
    messages = [
        HumanMessage(content="Show the top 5 brokers by claim amount", id="question"),
        HumanMessage(content="approve abc123", id="approval"),
    ]

    assert _previous_unapproved_user_message(messages) == "Show the top 5 brokers by claim amount"


def test_previous_unapproved_user_message_returns_none_without_business_question() -> None:
    messages = [HumanMessage(content="approve abc123", id="approval")]

    assert _previous_unapproved_user_message(messages) is None
