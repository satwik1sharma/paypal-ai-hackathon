"""Minimal Claude agent loop with PayPal tools. A starting point, not the product."""

import logging
from dataclasses import dataclass, field

import anthropic
from anthropic.types.beta import BetaMessageParam, BetaToolResultBlockParam

from paypal_ai_hackathon.config import get_settings
from paypal_ai_hackathon.paypal_tools import PayPalTools
from paypal_ai_hackathon.tracing import get_tracer

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a payments assistant operating a PayPal *sandbox* merchant account.
Use the PayPal tools to act, not just advise. Before any action that moves money or contacts a
customer (capturing an order, sending an invoice), state exactly what you are about to do.
When a tool fails, report the PayPal error plainly instead of guessing."""

MAX_TURNS = 10


@dataclass
class AgentResult:
    text: str
    stop_reason: str | None
    tool_calls: list[str] = field(default_factory=list)


def run_agent(prompt: str, tools: PayPalTools | None = None) -> AgentResult:
    settings = get_settings()
    tools = tools or PayPalTools()
    client = anthropic.Anthropic()
    messages: list[BetaMessageParam] = [{"role": "user", "content": prompt}]
    called: list[str] = []

    with get_tracer().start_as_current_span("agent.run") as span:
        span.set_attribute("openinference.span.kind", "AGENT")
        span.set_attribute("input.value", prompt)

        for _ in range(MAX_TURNS):
            response = client.beta.messages.create(
                model=settings.claude_model,
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                tools=tools.definitions(),
                messages=messages,
                output_config={"effort": settings.claude_effort},
                # Server-side refusal fallback: reroutes a declined turn instead of failing it.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
            # Append the full content (incl. thinking blocks) unchanged; never edit earlier turns.
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                text = "".join(b.text for b in response.content if b.type == "text")
                span.set_attribute("output.value", text)
                return AgentResult(text=text, stop_reason=response.stop_reason, tool_calls=called)

            results: list[BetaToolResultBlockParam] = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                called.append(block.name)
                try:
                    output = tools.run(block.name, block.input)
                    results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
                except Exception as exc:  # surface PayPal errors to Claude rather than crashing the loop
                    log.warning("PayPal tool %s failed: %s", block.name, exc)
                    results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": str(exc), "is_error": True}
                    )
            # All tool results go back in ONE user message (keeps parallel tool calls working).
            messages.append({"role": "user", "content": results})

    return AgentResult(text="Stopped: hit MAX_TURNS.", stop_reason="max_turns", tool_calls=called)
