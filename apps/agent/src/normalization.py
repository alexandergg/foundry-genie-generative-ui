from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class NormalizationWarning:
    code: str
    message: str

    def to_payload(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class VisualMeta:
    visual_id: str
    source: str
    generated_at: datetime
    row_count: int
    approval_request_id: str | None = None
    trace_id: str | None = None
    warnings: list[NormalizationWarning] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "visualId": self.visual_id,
            "source": self.source,
            "generatedAt": self.generated_at.isoformat().replace("+00:00", "Z"),
            "rowCount": self.row_count,
            "warnings": [warning.to_payload() for warning in self.warnings],
        }
        if self.approval_request_id:
            payload["approvalRequestId"] = self.approval_request_id
        if self.trace_id:
            payload["traceId"] = self.trace_id
        return payload


def build_visual_meta(
    component_name: str,
    index: int,
    *,
    source: str,
    row_count: int,
    generated_at: datetime | None = None,
    approval_request_id: str | None = None,
    trace_id: str | None = None,
    warnings: list[NormalizationWarning] | None = None,
) -> VisualMeta:
    safe_name = component_name.replace("_", "-").replace(" ", "-")
    return VisualMeta(
        visual_id=f"{safe_name}-{index + 1}",
        source=source,
        generated_at=generated_at or datetime.now(timezone.utc),
        row_count=row_count,
        approval_request_id=approval_request_id,
        trace_id=trace_id,
        warnings=warnings or [],
    )
