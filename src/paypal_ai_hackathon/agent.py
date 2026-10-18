"""Minimal OpenAI agent loop with PayPal tools. A starting point, not the product."""

import json
import logging
from dataclasses import dataclass, field

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from paypal_ai_hackathon.config import get_settings
from paypal_ai_hackathon.paypal_tools import PayPalTools
from paypal_ai_hackathon.tracing import get_tracer

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a payments assistant operating a PayPal *sandbox* merchant account.
Use the PayPal tools to act, not just advise. Before any action that moves money or contacts a
customer (capturing an order, sending an invoice), state exactly what you are about to do.
When a tool fails, report the PayPal error plainly instead of guessing."""

MAX_TURNS = 10


def openai_client() -> OpenAI:
    """OpenAI client keyed from settings (the SDK alone only reads os.environ, not .env)."""
    key = get_settings().openai_api_key.get_secret_value()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set in .env")
    return OpenAI(api_key=key)


@dataclass
class AgentResult:
    text: str
    finish_reason: str | None
    tool_calls: list[str] = field(default_factory=list)


def run_agent(prompt: str, tools: PayPalTools | None = None, model: str | None = None) -> AgentResult:
    settings = get_settings()
    tools = tools or PayPalTools()
    client = openai_client()
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    called: list[str] = []

    with get_tracer().start_as_current_span("agent.run") as span:
        span.set_attribute("openinference.span.kind", "AGENT")
        span.set_attribute("input.value", prompt)

        for _ in range(MAX_TURNS):
            response = client.chat.completions.create(
                model=model or settings.openai_model,
                messages=messages,
                tools=tools.definitions(),
            )
            choice = response.choices[0]
            msg = choice.message
            messages.append(msg.model_dump(exclude_none=True))

            if not msg.tool_calls:
                text = msg.content or ""
                span.set_attribute("output.value", text)
                return AgentResult(text=text, finish_reason=choice.finish_reason, tool_calls=called)

            for call in msg.tool_calls:
                called.append(call.function.name)
                try:
                    output = tools.run(call.function.name, json.loads(call.function.arguments or "{}"))
                except Exception as exc:  # surface PayPal errors to the model rather than crashing the loop
                    log.warning("PayPal tool %s failed: %s", call.function.name, exc)
                    output = f"ERROR: {exc}"
                # Every tool_call_id must get exactly one "tool" message back.
                messages.append({"role": "tool", "tool_call_id": call.id, "content": output})

    return AgentResult(text="Stopped: hit MAX_TURNS.", finish_reason="max_turns", tool_calls=called)
