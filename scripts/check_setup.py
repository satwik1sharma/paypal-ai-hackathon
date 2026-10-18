"""Verify local setup: env vars, PayPal sandbox OAuth, OpenAI API, Phoenix collector.

Run: uv run python scripts/check_setup.py
"""

import httpx
from rich.console import Console

from paypal_ai_hackathon.agent import openai_client
from paypal_ai_hackathon.config import get_settings
from paypal_ai_hackathon.tracing import setup_tracing

console = Console()


def check(label: str, fn) -> bool:
    try:
        detail = fn()
        console.print(f"[green]✔[/green] {label}" + (f" [dim]{detail}[/dim]" if detail else ""))
        return True
    except Exception as exc:
        console.print(f"[red]✘[/red] {label}: {exc}")
        return False


def paypal_token() -> str:
    s = get_settings()
    if not s.paypal_client_id:
        raise RuntimeError("PAYPAL_CLIENT_ID is empty in .env")
    r = httpx.post(
        f"{s.paypal_base_url}/v1/oauth2/token",
        auth=(s.paypal_client_id, s.paypal_client_secret.get_secret_value()),
        data={"grant_type": "client_credentials"},
        timeout=15,
    )
    r.raise_for_status()
    return f"{s.paypal_environment}, token expires in {r.json()['expires_in']}s"


def openai_ping() -> str:
    s = get_settings()
    r = openai_client().chat.completions.create(
        model=s.openai_model,
        max_tokens=10,
        messages=[{"role": "user", "content": "Reply with exactly: pong"}],
    )
    return f"{s.openai_model} -> {(r.choices[0].message.content or '').strip()!r}"


def phoenix_up() -> str:
    s = get_settings()
    base = s.phoenix_collector_endpoint.removesuffix("/v1/traces")
    httpx.get(base, timeout=3).raise_for_status()
    return f"UI at {base}"


if __name__ == "__main__":
    phoenix_ok = check("Phoenix collector reachable", phoenix_up)
    if phoenix_ok:
        setup_tracing()
    results = [phoenix_ok, check("PayPal sandbox OAuth", paypal_token), check("OpenAI API", openai_ping)]
    if phoenix_ok:
        from opentelemetry import trace

        trace.get_tracer_provider().force_flush()
        console.print("[dim]OpenAI ping trace sent to Phoenix.[/dim]")
    raise SystemExit(0 if all(results) else 1)
