from __future__ import annotations

from collections.abc import AsyncIterator

from ag_ui.core.types import RunAgentInput
from ag_ui.encoder import EventEncoder
from azure.ai.agentserver.invocations import InvocationAgentServerHost
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse

from main import build_ag_ui_agent, settings

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
    request_agent = build_ag_ui_agent()

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
