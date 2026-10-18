# PayPal AI Hackathon

Entry for [Build What's Next with PayPal and AI](https://paypalaihackathon.devpost.com/) (submissions close **12 Nov 2026, 12:00 PT**).

> **Status:** setup done, idea in brainstorming. This README becomes the judges' setup guide once the idea is chosen.

Built with the PayPal developer platform (sandbox, [Agent Toolkit](https://github.com/paypal/agent-toolkit)) and Claude (Anthropic API), traced with [Arize Phoenix](https://phoenix.arize.com/).

## Quick start

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env              # then fill in Claude + PayPal sandbox keys
uvx arize-phoenix serve           # tracing UI on http://localhost:6006 (separate terminal)
uv run python scripts/check_setup.py
uv run paypal-ai-hackathon "Create a PayPal order for \$12 for a coffee subscription and give me the approval link"
```

API server: `uv run uvicorn paypal_ai_hackathon.api:app --reload` → http://localhost:8000/docs

## License

MIT, see [LICENSE](LICENSE).
