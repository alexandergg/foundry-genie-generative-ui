from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from .config import Settings


@dataclass
class FoundryAgentResponse:
    answer: str
    conversation_id: str | None = None


class FoundryAgentClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _agent_reference(self) -> dict[str, str]:
        reference = {"name": self.settings.agent_name or "", "type": "agent_reference"}
        if self.settings.agent_version and self.settings.agent_version.startswith(f"{self.settings.agent_name}:"):
            reference["version"] = self.settings.agent_version.split(":", 1)[1]
        return reference

    def _approval_responses(self, response: Any) -> list[Any]:
        try:
            from openai.types.responses.response_input_param import McpApprovalResponse
        except ImportError as exc:
            raise RuntimeError("OpenAI response types are missing from the installed SDK.") from exc

        approvals: list[Any] = []
        for item in getattr(response, "output", []) or []:
            if getattr(item, "type", None) == "mcp_approval_request" and getattr(item, "id", None):
                approvals.append(
                    McpApprovalResponse(
                        type="mcp_approval_response",
                        approve=True,
                        approval_request_id=item.id,
                    )
                )
        return approvals

    def _response_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text

        fragments: list[str] = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text = getattr(content, "text", None)
                if text:
                    fragments.append(text)
        if fragments:
            return "\n".join(fragments)

        pending_approvals = [getattr(item, "name", "MCP tool") for item in getattr(response, "output", []) or [] if getattr(item, "type", None) == "mcp_approval_request"]
        if pending_approvals:
            return "The query requires MCP approval for: " + ", ".join(pending_approvals)

        return "Foundry did not return final text for this query."

    def _complete_mcp_approvals(self, openai_client: Any, response: Any) -> Any:
        for _ in range(self.settings.mcp_approval_rounds):
            approvals = self._approval_responses(response)
            if not approvals:
                break
            response = openai_client.responses.create(
                input=approvals,
                previous_response_id=response.id,
                extra_body={"agent_reference": self._agent_reference()},
            )

        pending_approvals = self._approval_responses(response)
        if pending_approvals:
            pending_names = [
                getattr(item, "name", "MCP tool")
                for item in getattr(response, "output", []) or []
                if getattr(item, "type", None) == "mcp_approval_request"
            ]
            raise RuntimeError(
                "Foundry/Genie kept requesting MCP approvals after "
                f"{self.settings.mcp_approval_rounds} rounds: {', '.join(pending_names)}"
            )
        return response

    def _looks_transient(self, answer: str) -> bool:
        lowered = answer.lower()
        transient_markers = ["in progress", "still running", "continues running", "en proceso", "está en proceso", "continúa en ejecución", "sigue ejecut", "puede deberse"]
        warehouse_markers = ["warehouse", "sql warehouse", "stopped", "start", "warming", "parado", "arrancado"]
        return any(marker in lowered for marker in transient_markers) and any(marker in lowered for marker in warehouse_markers)

    def _is_missing_mcp_approval_error(self, exc: Exception) -> bool:
        message = str(exc).lower()
        return "mcp approval requests" in message and "do not have an approval" in message

    def _genie_business_prompt(self, question: str, has_conversation_context: bool = False) -> str:
        context_instruction = (
            "You are continuing the same Foundry conversation. First use prior messages, prior Genie results and prior markdown tables when they are sufficient. "
            "Only call Databricks Genie again when the user asks for new data, new filters, missing columns or a fresh calculation. "
            if has_conversation_context
            else "This is the first business query in this Foundry conversation. "
        )
        return (
            f"{context_instruction}"
            "If you do call Databricks Genie, start a new Genie query/conversation; do not reuse Databricks Genie conversation_id values or IDs such as 1. "
            "Prefer the vw_uc3_genie_exposure_claims view and answer in English. "
            "When aggregated metrics are available, return a markdown table with stable columns and numeric values; do not invent data. "
            f"User question: {question}"
        )

    def ask(self, question: str, conversation_id: str | None = None) -> FoundryAgentResponse:
        if not self.settings.project_endpoint:
            raise RuntimeError("FOUNDRY_PROJECT_ENDPOINT is not configured and .foundry metadata was not found.")
        if not self.settings.agent_name:
            raise RuntimeError("FOUNDRY_AGENT_NAME is not configured.")

        try:
            from azure.ai.projects import AIProjectClient
            from azure.identity import DefaultAzureCredential
        except ImportError as exc:
            raise RuntimeError("Azure Foundry SDK dependencies are missing. Run `pip install -e apps/agent`.") from exc

        credential = DefaultAzureCredential()
        project_client = AIProjectClient(endpoint=self.settings.project_endpoint, credential=credential)

        with project_client.get_openai_client() as openai_client:
            last_error: Exception | None = None
            for attempt in range(2):
                active_conversation_id = conversation_id if attempt == 0 and conversation_id else openai_client.conversations.create().id
                try:
                    response = openai_client.responses.create(
                        conversation=active_conversation_id,
                        input=self._genie_business_prompt(question, has_conversation_context=attempt == 0 and bool(conversation_id)),
                        extra_body={"agent_reference": self._agent_reference()},
                    )
                    response = self._complete_mcp_approvals(openai_client, response)

                    answer = self._response_text(response)
                    for _ in range(self.settings.transient_response_retries):
                        if not self._looks_transient(answer):
                            break
                        time.sleep(3)
                        response = openai_client.responses.create(
                            input=(
                                "The SQL Warehouse is already active. Continue the original query, "
                                "keep polling Genie if needed and return the final data-backed result. "
                                "Do not answer that the warehouse is stopped unless the technical error explicitly confirms it."
                            ),
                            previous_response_id=response.id,
                            extra_body={"agent_reference": self._agent_reference()},
                        )
                        response = self._complete_mcp_approvals(openai_client, response)
                        answer = self._response_text(response)

                    return FoundryAgentResponse(
                        answer=answer,
                        conversation_id=active_conversation_id,
                    )
                except Exception as exc:
                    last_error = exc
                    if conversation_id and attempt == 0 and self._is_missing_mcp_approval_error(exc):
                        continue
                    raise

            raise last_error or RuntimeError("Foundry/Genie query failed without returning an error.")
