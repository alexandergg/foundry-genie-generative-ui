from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

UI_EVENT_SCHEMA_VERSION = "risk-ui/v1"

UiEventKind = Literal[
    "reasoning.started",
    "reasoning.completed",
    "plan.created",
    "query.started",
    "query.completed",
    "normalization.started",
    "normalization.completed",
    "visualization.proposed",
    "visualization.rendered",
    "provenance.attached",
    "followups.suggested",
    "error.safe",
]

UiEventPhase = Literal["supervise", "query", "normalize", "visualize", "complete", "error"]


@dataclass(frozen=True)
class UiEventEnvelopeV1:
    kind: UiEventKind
    phase: UiEventPhase
    payload: dict[str, Any]
    event_id: str
    timestamp: str
    run_id: str | None = None
    thread_id: str | None = None
    schema_version: str = UI_EVENT_SCHEMA_VERSION

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schemaVersion": self.schema_version,
            "eventId": self.event_id,
            "kind": self.kind,
            "phase": self.phase,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }
        if self.run_id:
            payload["runId"] = self.run_id
        if self.thread_id:
            payload["threadId"] = self.thread_id
        return payload


def build_ui_event(
    kind: UiEventKind,
    phase: UiEventPhase,
    payload: dict[str, Any],
    *,
    run_id: str | None = None,
    thread_id: str | None = None,
) -> UiEventEnvelopeV1:
    return UiEventEnvelopeV1(
        kind=kind,
        phase=phase,
        payload=payload,
        event_id=f"ui-{uuid4().hex[:12]}",
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        run_id=run_id,
        thread_id=thread_id,
    )
