from __future__ import annotations

import pytest

from src.component_registry import CONTROLLED_COMPONENT_NAMES, validate_component_name
from src.ui_event_contract import UI_EVENT_SCHEMA_VERSION, build_ui_event
from src.visualization_mapper import build_component_calls


def test_visualization_mapper_only_emits_registered_components() -> None:
    answer = """
| broker | total_exposure_eur | total_claim_amount_eur |
| --- | ---: | ---: |
| Broker A | 1000 | 100 |
"""

    calls = build_component_calls("compare exposure and claims by broker", answer)

    assert {call.name for call in calls}.issubset(set(CONTROLLED_COMPONENT_NAMES))


def test_validate_component_name_rejects_unknown_components() -> None:
    with pytest.raises(ValueError, match="Unsupported controlled UI component"):
        validate_component_name("freeformHtml")


def test_build_ui_event_creates_versioned_payload() -> None:
    event = build_ui_event("query.started", "query", {"question": "Show exposure"}, run_id="run-1")

    assert event.to_payload() == {
        "schemaVersion": UI_EVENT_SCHEMA_VERSION,
        "eventId": event.event_id,
        "runId": "run-1",
        "kind": "query.started",
        "phase": "query",
        "timestamp": event.timestamp,
        "payload": {"question": "Show exposure"},
    }


def test_agent_status_card_is_no_longer_a_controlled_component() -> None:
    from src.component_registry import CONTROLLED_COMPONENT_NAMES

    assert "agentStatusCard" not in CONTROLLED_COMPONENT_NAMES


def test_emit_ui_event_only_dispatches_risk_ui_event(monkeypatch) -> None:
    import asyncio

    import main

    dispatched: list[str] = []

    async def fake_dispatch(name, payload):  # noqa: ANN001
        dispatched.append(name)

    monkeypatch.setattr(main, "adispatch_custom_event", fake_dispatch)
    asyncio.run(main._emit_ui_event("query.started", "query", {"message": "hi"}))

    assert dispatched == ["risk_ui_event"]
    assert "manually_emit_message" not in dispatched
