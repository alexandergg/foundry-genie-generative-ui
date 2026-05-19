from __future__ import annotations

from collections.abc import AsyncIterator

from ag_ui.core.types import RunAgentInput
from ag_ui.encoder import EventEncoder
from azure.ai.agentserver.invocations import InvocationAgentServerHost
from copilotkit import LangGraphAGUIAgent
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse

from main import agent_graph, settings


def _build_agent() -> LangGraphAGUIAgent:
    return LangGraphAGUIAgent(
        name="default",
        description="Risk Exposure Foundry/Genie Generative UI agent",
        graph=agent_graph,
    )


app = InvocationAgentServerHost()


@app.invoke_handler
async def handle_invoke(request: Request) -> Response:
    try:
        payload = await request.json()
        input_data = RunAgentInput.model_validate(payload)
    except (ValueError, ValidationError) as exc:
        return JSONResponse(
            {"error": "invalid_ag_ui_request", "detail": str(exc)},
            status_code=400,
        )

    encoder = EventEncoder(accept=request.headers.get("accept", ""))
    request_agent = _build_agent()

    async def event_generator() -> AsyncIterator[str]:
        async for event in request_agent.run(input_data):  # type: ignore[no-untyped-call]
            yield encoder.encode(event)

    return StreamingResponse(
        event_generator(),
        media_type=encoder.get_content_type(),
        headers={
            "x-foundry-agent": settings.agent_name,
            "x-ag-ui-agent": request_agent.name,
        },
    )


if __name__ == "__main__":
    app.run()
