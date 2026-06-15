"""OpenTelemetry tracing wiring for the hosted AG-UI agent.

The `azure-ai-agentserver-invocations` runtime already configures the OTel
exporter and correlates spans to this agent inside the Foundry container, but it
only captures the bare outer ``invoke_agent`` span. Attaching
``AzureAIOpenTelemetryTracer`` (from ``langchain-azure-ai[opentelemetry]``) as a
LangChain callback makes the graph emit the GenAI spans Foundry needs — model
calls, tool calls, token usage — so Traces, cost and evaluators light up.

The tracer auto-detects the App Insights connection string from
``APPLICATIONINSIGHTS_CONNECTION_STRING`` (injected by Foundry) or from the
project endpoint. Everything degrades to a no-op locally, so dev and tests never
need Azure wiring.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

_DISABLED_VALUES = {"0", "false", "no", "off"}


def tracing_enabled(env: Mapping[str, str] | None = None) -> bool:
    """Whether the agent should emit traces.

    An explicit ``RISK_TRACING_ENABLED`` flag wins (a kill switch in both
    directions); otherwise tracing turns on only when there is somewhere to
    export to — the App Insights connection string Foundry injects, or a project
    endpoint the tracer can resolve one from.
    """
    env = os.environ if env is None else env
    explicit = env.get("RISK_TRACING_ENABLED", "").strip()
    if explicit:
        return explicit.lower() not in _DISABLED_VALUES
    return bool(
        env.get("APPLICATIONINSIGHTS_CONNECTION_STRING") or env.get("FOUNDRY_PROJECT_ENDPOINT") or env.get("AZURE_AI_PROJECT_ENDPOINT")
    )


def build_trace_callbacks(agent_id: str, env: Mapping[str, str] | None = None) -> list[Any]:
    """LangChain callbacks that emit OTel GenAI spans, or ``[]`` when tracing is off.

    ``agent_id`` is stamped onto spans as ``gen_ai.agent.id`` so Foundry attributes
    them to this agent. Safe to call anywhere: returns ``[]`` when disabled or when
    the optional ``langchain-azure-ai[opentelemetry]`` tracer isn't installed.
    """
    env = os.environ if env is None else env
    if not tracing_enabled(env):
        return []
    try:
        from langchain_azure_ai.callbacks.tracers import AzureAIOpenTelemetryTracer
    except ImportError:
        return []
    return [
        AzureAIOpenTelemetryTracer(
            connection_string=env.get("APPLICATIONINSIGHTS_CONNECTION_STRING") or None,
            project_endpoint=env.get("FOUNDRY_PROJECT_ENDPOINT") or env.get("AZURE_AI_PROJECT_ENDPOINT") or None,
            agent_id=agent_id,
        )
    ]
