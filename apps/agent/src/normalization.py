from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class NormalizationWarning:
    code: str
    message: str

    def to_payload(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


def build_dataset_provenance(
    *,
    source: str,
    row_count: int,
    generated_at: datetime | None = None,
    approval_request_id: str | None = None,
    trace_id: str | None = None,
    warnings: list[NormalizationWarning] | None = None,
) -> dict[str, Any]:
    """Dataset-level provenance shared by every visual derived from a Genie result.

    The frontend adds a per-visual ``visualId`` when it renders each card, so this
    payload intentionally omits it.
    """
    payload: dict[str, Any] = {
        "source": source,
        "generatedAt": (generated_at or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z"),
        "rowCount": row_count,
        "warnings": [warning.to_payload() for warning in (warnings or [])],
    }
    if approval_request_id:
        payload["approvalRequestId"] = approval_request_id
    if trace_id:
        payload["traceId"] = trace_id
    return payload
