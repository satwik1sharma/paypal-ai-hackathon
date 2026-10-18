"""Phoenix (OpenInference / OpenTelemetry) tracing setup.

Call `setup_tracing()` once at process start, before creating any OpenAI client.
Every OpenAI call is then traced automatically; wrap your own steps with `tracer.start_as_current_span`.
"""

import logging

from opentelemetry import trace

from paypal_ai_hackathon.config import get_settings

log = logging.getLogger(__name__)
_configured = False


def setup_tracing() -> None:
    global _configured
    settings = get_settings()
    if _configured or not settings.tracing_enabled:
        return

    from phoenix.otel import register

    register(
        endpoint=settings.phoenix_collector_endpoint,
        project_name=settings.phoenix_project_name,
        batch=True,
        auto_instrument=True,  # picks up openinference-instrumentation-openai
        verbose=False,
    )
    _configured = True
    log.info("Phoenix tracing -> %s (project %s)", settings.phoenix_collector_endpoint, settings.phoenix_project_name)


def get_tracer(name: str = "paypal_ai_hackathon") -> trace.Tracer:
    return trace.get_tracer(name)
