"""PayPal AI Hackathon project."""

import logging
import sys


def main() -> None:
    """CLI: `uv run paypal-ai-hackathon "Create a $10 order for a coffee"`."""
    from rich.console import Console

    from paypal_ai_hackathon.agent import run_agent
    from paypal_ai_hackathon.tracing import setup_tracing

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if len(sys.argv) < 2:
        sys.exit('usage: paypal-ai-hackathon "<prompt>"')

    setup_tracing()
    result = run_agent(" ".join(sys.argv[1:]))
    console = Console()
    console.print(result.text)
    console.print(f"[dim]finish_reason={result.finish_reason} tools={result.tool_calls}[/dim]")
