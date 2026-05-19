from __future__ import annotations

import pytest

from src.config import _env_bool, load_settings


def test_env_bool_accepts_common_true_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FEATURE_ENABLED", "yes")

    assert _env_bool("FEATURE_ENABLED", False) is True


def test_env_bool_uses_default_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FEATURE_ENABLED", raising=False)

    assert _env_bool("FEATURE_ENABLED", True) is True


def test_risk_genie_environment_variables_override_foundry_reserved_names(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RISK_GENIE_PROJECT_ENDPOINT", "https://example.services.ai.azure.com/api/projects/demo")
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://legacy.services.ai.azure.com/api/projects/demo")
    monkeypatch.setenv("RISK_GENIE_AGENT_NAME", "risk-agent")
    monkeypatch.setenv("FOUNDRY_AGENT_NAME", "legacy-agent")
    monkeypatch.setenv("RISK_GENIE_AGENT_VERSION", "risk-agent:2")
    monkeypatch.setenv("RISK_GENIE_MCP_APPROVAL_ROUNDS", "7")
    monkeypatch.setenv("RISK_GENIE_REQUIRE_HUMAN_DATA_APPROVAL", "false")
    monkeypatch.setenv("RISK_GENIE_TRANSIENT_RESPONSE_RETRIES", "3")

    settings = load_settings()

    assert settings.project_endpoint == "https://example.services.ai.azure.com/api/projects/demo"
    assert settings.agent_name == "risk-agent"
    assert settings.agent_version == "risk-agent:2"
    assert settings.mcp_approval_rounds == 7
    assert settings.require_human_data_approval is False
    assert settings.transient_response_retries == 3
