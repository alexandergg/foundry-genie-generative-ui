"""Reconstruct the current dashboard state from the agent's own emitted tool calls.

The frontend generates a deterministic visual id from the addVisual args
(`vis-<datasetId>-<type>-<dimension>-<measure>`). We mirror that formula here so
the agent can reference existing visuals by the same id when removing or
re-typing them, without depending on frontend context being forwarded back.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from langchain_core.messages import AnyMessage

_DASHBOARD_TOOLS = {
    "cacheDataset",
    "addVisual",
    "removeVisual",
    "changeVisualType",
    "reorderVisuals",
    "clearDashboard",
    "spotlightVisual",
    "setPresentationMode",
}


def visual_id_for(args: dict[str, Any]) -> str:
    measure = args.get("measure")
    measure_str = "_".join(str(m) for m in measure) if isinstance(measure, list) else (str(measure) if measure else "v")
    dimension = args.get("dimension") or "x"
    return f"vis-{args.get('datasetId')}-{args.get('type')}-{dimension}-{measure_str}"


def _tool_calls(message: AnyMessage) -> list[dict[str, Any]]:
    calls = getattr(message, "tool_calls", None) or []
    return [call for call in calls if isinstance(call, dict)]


def extract_dashboard_context(messages: Sequence[AnyMessage]) -> dict[str, Any]:
    """Replay emitted dashboard tool calls into the current datasets + visuals + view state."""
    datasets: dict[str, dict[str, Any]] = {}
    visuals: dict[str, dict[str, Any]] = {}
    view: dict[str, Any] = {"spotlightVisualId": None, "presentationMode": False}

    for message in messages:
        for call in _tool_calls(message):
            name = call.get("name")
            if name not in _DASHBOARD_TOOLS:
                continue
            args = call.get("args") or {}
            if name == "cacheDataset":
                datasets[args["id"]] = {
                    "id": args["id"],
                    "title": args.get("title"),
                    "columns": [{"key": column.get("key"), "role": column.get("role")} for column in args.get("columns", [])],
                }
            elif name == "addVisual":
                vid = visual_id_for(args)
                visuals[vid] = {
                    "id": vid,
                    "type": args.get("type"),
                    "dimension": args.get("dimension"),
                    "measure": args.get("measure"),
                    "title": args.get("title"),
                    "datasetId": args.get("datasetId"),
                }
            elif name == "removeVisual":
                target_id = args.get("id")
                if isinstance(target_id, str):
                    visuals.pop(target_id, None)
                    if view["spotlightVisualId"] == target_id:
                        view["spotlightVisualId"] = None
            elif name == "changeVisualType":
                target_id = args.get("id")
                target = visuals.get(target_id) if isinstance(target_id, str) else None
                if target is not None:
                    target["type"] = args.get("type")
            elif name == "clearDashboard":
                visuals.clear()
                view["spotlightVisualId"] = None
            elif name == "spotlightVisual":
                target_id = args.get("id")
                view["spotlightVisualId"] = target_id if isinstance(target_id, str) else None
            elif name == "setPresentationMode":
                view["presentationMode"] = bool(args.get("enabled"))

    return {"datasets": list(datasets.values()), "visuals": list(visuals.values()), "view": view}
