from __future__ import annotations

from typing import Any

from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel

from .config import Settings, load_settings

_chat_model: Any | None = None


def build_chat_model(settings: Settings) -> AzureAIChatCompletionsModel:
    if not settings.model_endpoint:
        raise RuntimeError("RISK_MODEL_ENDPOINT is not configured. Copy .env.example to .env and fill it in.")

    if settings.model_api_key:
        credential: object = settings.model_api_key
    else:
        from azure.identity import DefaultAzureCredential

        credential = DefaultAzureCredential()

    return AzureAIChatCompletionsModel(
        endpoint=settings.model_endpoint,
        credential=credential,
        model=settings.model_deployment,
    )


def get_chat_model() -> Any:
    """Process-wide model singleton, built lazily so import never needs Azure."""
    global _chat_model
    if _chat_model is None:
        _chat_model = build_chat_model(load_settings())
    return _chat_model
