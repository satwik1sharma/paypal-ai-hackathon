"""Expose PayPal Agent Toolkit tools to Claude.

The toolkit ships adapters for OpenAI / LangChain / CrewAI / Bedrock but not for the Anthropic SDK,
so this module converts its shared tool registry into Anthropic tool definitions and dispatches
Claude's `tool_use` calls back to `PayPalAPI.run`.
"""

import json
from typing import Any

from anthropic.types import ToolParam
from paypal_agent_toolkit.shared.api import PayPalAPI
from paypal_agent_toolkit.shared.configuration import Configuration, Context, is_tool_allowed
from paypal_agent_toolkit.shared.tools import tools as TOOLKIT_TOOLS

from paypal_ai_hackathon.config import get_settings
from paypal_ai_hackathon.tracing import get_tracer

# Start narrow; widen per feature. Keys are toolkit "products", values are toolkit "actions".
DEFAULT_ACTIONS: dict[str, dict[str, bool]] = {
    "orders": {"create": True, "get": True, "capture": True},
    "invoices": {"create": True, "list": True, "get": True, "send": True},
    "transactions": {"list": True},
}


class PayPalTools:
    def __init__(self, actions: dict[str, dict[str, bool]] | None = None) -> None:
        settings = get_settings()
        if not settings.paypal_client_id or not settings.paypal_client_secret.get_secret_value():
            raise RuntimeError("PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET are not set (see .env.example)")

        context = Context(sandbox=settings.paypal_sandbox)
        configuration = Configuration(actions=actions or DEFAULT_ACTIONS, context=context)
        self._enabled = [t for t in TOOLKIT_TOOLS if is_tool_allowed(t, configuration)]
        self._api = PayPalAPI(
            client_id=settings.paypal_client_id,
            secret=settings.paypal_client_secret.get_secret_value(),
            context=context,
        )

    @property
    def names(self) -> list[str]:
        return [t["method"] for t in self._enabled]

    def definitions(self) -> list[ToolParam]:
        return to_anthropic_tools(self._enabled)

    def run(self, name: str, tool_input: dict[str, Any]) -> str:
        """Execute one PayPal tool call. Blocking (the toolkit uses `requests`)."""
        if name not in self.names:
            raise ValueError(f"PayPal tool {name!r} is not enabled")
        with get_tracer().start_as_current_span(f"paypal.{name}") as span:
            span.set_attribute("openinference.span.kind", "TOOL")
            span.set_attribute("tool.name", name)
            span.set_attribute("input.value", json.dumps(tool_input))
            result = self._api.run(name, tool_input)
            span.set_attribute("output.value", result if isinstance(result, str) else json.dumps(result))
            return result if isinstance(result, str) else json.dumps(result)


def to_anthropic_tools(toolkit_tools: list[dict[str, Any]]) -> list[ToolParam]:
    return [
        {
            "name": t["method"],
            "description": t["description"].strip(),
            "input_schema": t["args_schema"].model_json_schema(),
        }
        for t in toolkit_tools
    ]
