"""Live-model integration test for the dynamic (freeform) A2UI path.

Opt-in: hits the real Foundry model, so it is skipped unless
``RUN_LIVE_MODEL_TESTS=1`` is set AND a model endpoint resolves. Run it with::

    RUN_LIVE_MODEL_TESTS=1 .venv/bin/python -m pytest tests/test_live_dynamic.py -q

This guards the catalog-binding fix end-to-end against the actual model: the
``@ag-ui/a2ui-middleware`` stamps ``createSurface`` with the model's
``render_a2ui`` ``catalogId`` argument, defaulting to the v0.9 *basic* catalog
when absent. The frontend registers only this app's catalog
(``includeBasicCatalog: false``), so a missing ``catalogId`` renders as
"Catalog not found". The unit tests prove the prompt pins the id; this test
proves the live model actually emits it.
"""

from __future__ import annotations

import json
import os

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.config import load_settings
from src.graph import RENDER_A2UI_TOOL_NAME, AgentState, generate_dynamic
from src.report_catalog import RISK_CATALOG_ID

_RUN_LIVE = os.getenv("RUN_LIVE_MODEL_TESTS") == "1" and bool(load_settings().model_endpoint)

pytestmark = pytest.mark.skipif(
    not _RUN_LIVE,
    reason="set RUN_LIVE_MODEL_TESTS=1 with a configured model endpoint to run live-model tests",
)

# Mirrors the render_a2ui tool the @ag-ui/a2ui-middleware injects in production:
# it exposes a `catalogId` parameter, so the model is allowed to emit it.
RENDER_A2UI_TOOL_WITH_CATALOG = {
    "name": RENDER_A2UI_TOOL_NAME,
    "description": "Render a dynamic A2UI v0.9 surface with structured parameters.",
    "parameters": {
        "type": "object",
        "properties": {
            "surfaceId": {"type": "string", "description": "Unique surface identifier."},
            "catalogId": {"type": "string", "description": "The catalog ID for the component catalog."},
            "components": {"type": "array", "description": "A2UI v0.9 component array.", "items": {"type": "object"}},
            "data": {"type": "object", "description": "Initial data model for the surface."},
        },
        "required": ["surfaceId", "components"],
    },
}

# A bare components array (no catalogId) — the shape that forces _catalog_id_from
# to fall back to the app's catalog, exactly as in the failing screenshot.
LIVE_SCHEMA = json.dumps([{"name": name} for name in ("Title", "Column", "Row", "Metric", "BarChart", "DashboardCard", "Badge")])


async def test_live_model_emits_custom_catalog_id() -> None:
    state: AgentState = {
        "messages": [HumanMessage(content="Compose a risk dashboard your way — pick the catalog components you think fit best")],
        "ag-ui": {"a2ui_schema": LIVE_SCHEMA, "tools": [RENDER_A2UI_TOOL_WITH_CATALOG]},
    }

    result = await generate_dynamic(state)

    message = result["messages"][-1]
    assert isinstance(message, AIMessage), f"unexpected message type: {message!r}"
    assert message.tool_calls, f"model did not call render_a2ui; content={message.content!r}"

    render_calls = [c for c in message.tool_calls if c["name"] == RENDER_A2UI_TOOL_NAME]
    assert render_calls, f"no render_a2ui call among {[c['name'] for c in message.tool_calls]}"

    catalog_ids = [c["args"].get("catalogId") for c in render_calls]
    # Every composed surface must bind to this app's catalog, never the basic one.
    assert all(cid == RISK_CATALOG_ID for cid in catalog_ids), f"catalogId(s) emitted: {catalog_ids}"
