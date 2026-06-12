from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    model_endpoint: str
    model_deployment: str
    model_api_key: str | None


def _env_first(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def load_settings() -> Settings:
    """Resolve the Foundry model connection.

    `RISK_MODEL_*` are the primary names because Foundry Hosted Agent
    containers reserve the `FOUNDRY_*` prefix; the `FOUNDRY_MODEL_*` /
    `AZURE_AI_MODEL_*` names keep working for local development.
    """
    load_dotenv()
    return Settings(
        model_endpoint=_env_first("RISK_MODEL_ENDPOINT", "FOUNDRY_MODEL_ENDPOINT", "AZURE_AI_MODEL_ENDPOINT") or "",
        model_deployment=_env_first("RISK_MODEL_DEPLOYMENT", "FOUNDRY_MODEL_DEPLOYMENT", "AZURE_AI_MODEL_DEPLOYMENT") or "gpt-4o",
        model_api_key=_env_first("RISK_MODEL_API_KEY", "FOUNDRY_MODEL_API_KEY", "AZURE_AI_MODEL_API_KEY"),
    )
