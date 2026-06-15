"""Declarative Generative UI demo agent — local AG-UI bridge entrypoint.

Band 02 of the spectrum (course L4): A2UI fixed + dynamic schemas over the
app's component catalog. The graph lives in `src/graph.py`; this module only
wires it to FastAPI for local development. `hosted_main.py` is the Foundry
Hosted Agent (Invocations protocol) entrypoint.
"""

from __future__ import annotations

import os
from typing import Any

from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from fastapi import FastAPI

from src.config import load_settings
from src.graph import agent_graph, build_ag_ui_agent

APP_TITLE = "Declarative A2UI Report Agent"

settings = load_settings()
app = FastAPI(title=APP_TITLE)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "modelDeployment": settings.model_deployment,
        "layouts": ["executive", "brief", "freeform (dynamic)"],
    }


add_langgraph_fastapi_endpoint(app=app, agent=build_ag_ui_agent(), path="/")

__all__ = ["agent_graph", "app", "build_ag_ui_agent", "settings"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8124")), reload=True)
