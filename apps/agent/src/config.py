from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml
from dotenv import load_dotenv

DEMO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_METADATA_PATH = DEMO_ROOT / ".foundry" / "agent-metadata.yaml"
METADATA_PATH = Path(os.getenv("FOUNDRY_METADATA_PATH", str(DEFAULT_METADATA_PATH))).expanduser().resolve()


@dataclass(frozen=True)
class Settings:
    project_endpoint: str
    agent_name: str
    agent_version: str | None
    databricks_sql_warehouse_name: str | None
    transient_response_retries: int


def _load_metadata() -> dict[str, Any]:
    if not METADATA_PATH.exists():
        return {}
    with METADATA_PATH.open("r", encoding="utf-8") as fh:
        loaded = yaml.safe_load(fh) or {}
    return cast(dict[str, Any], loaded)


def _env_first(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return value
    return None


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_settings() -> Settings:
    load_dotenv()
    metadata = _load_metadata()
    env_name = metadata.get("defaultEnvironment", "dev")
    env = (metadata.get("environments") or {}).get(env_name, {})

    return Settings(
        project_endpoint=_env_first("RISK_GENIE_PROJECT_ENDPOINT", "FOUNDRY_PROJECT_ENDPOINT") or env.get("projectEndpoint", ""),
        agent_name=_env_first("RISK_GENIE_AGENT_NAME", "FOUNDRY_AGENT_NAME") or env.get("agentName", "risk-exposure-genie-agent"),
        agent_version=_env_first("RISK_GENIE_AGENT_VERSION", "FOUNDRY_AGENT_VERSION") or env.get("databricksGenieAgentVersion"),
        databricks_sql_warehouse_name=os.getenv("DATABRICKS_SQL_WAREHOUSE_NAME") or env.get("databricksSqlWarehouseName"),
        transient_response_retries=int(_env_first("RISK_GENIE_TRANSIENT_RESPONSE_RETRIES", "FOUNDRY_TRANSIENT_RESPONSE_RETRIES") or "2"),
    )
