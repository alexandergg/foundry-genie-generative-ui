from __future__ import annotations

from src.observability import build_trace_callbacks, tracing_enabled

_FAKE_CONN = "InstrumentationKey=00000000-0000-0000-0000-000000000000;IngestionEndpoint=https://example.in.applicationinsights.azure.com/"


def test_tracing_disabled_when_no_export_target() -> None:
    assert tracing_enabled({}) is False


def test_tracing_enabled_with_app_insights_connection_string() -> None:
    assert tracing_enabled({"APPLICATIONINSIGHTS_CONNECTION_STRING": _FAKE_CONN}) is True


def test_tracing_enabled_with_project_endpoint() -> None:
    assert tracing_enabled({"FOUNDRY_PROJECT_ENDPOINT": "https://x.services.ai.azure.com/api/projects/p"}) is True


def test_explicit_flag_disables_even_with_connection_string() -> None:
    env = {"APPLICATIONINSIGHTS_CONNECTION_STRING": _FAKE_CONN, "RISK_TRACING_ENABLED": "false"}
    assert tracing_enabled(env) is False


def test_build_trace_callbacks_empty_when_disabled() -> None:
    assert build_trace_callbacks("risk-declarative-a2ui-hosted", env={}) == []


def test_build_trace_callbacks_returns_tracer_when_enabled() -> None:
    from langchain_azure_ai.callbacks.tracers import AzureAIOpenTelemetryTracer

    callbacks = build_trace_callbacks("risk-declarative-a2ui-hosted", env={"APPLICATIONINSIGHTS_CONNECTION_STRING": _FAKE_CONN})

    assert len(callbacks) == 1
    assert isinstance(callbacks[0], AzureAIOpenTelemetryTracer)
