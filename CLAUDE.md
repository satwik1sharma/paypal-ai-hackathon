# PayPal AI Hackathon

Entry for "Build What's Next with PayPal and AI" (Devpost). **Deadline: Thu 12 Nov 2026, 12:00 PT.**
Hard requirement: the project must *meaningfully* use both PayPal (sandbox) and AI. Judged on technical
implementation, design (a complete product, not a PoC), impact, innovation, and a demo video under 3 minutes.

**Status: ideation.** The product idea isn't chosen yet. Don't build product features until it is; keep
`src/` as a thin, working skeleton until then.

## Stack
- Python 3.13, managed **only** with `uv`. Never `pip install` and never edit `uv.lock` by hand.
- Claude via the official `anthropic` SDK (1.x). Default model `claude-opus-5-5` (set in `.env`).
- PayPal via `paypal-agent-toolkit` (sandbox), plus raw REST calls with `httpx` when the toolkit lacks an endpoint.
- Tracing via Arize Phoenix (OpenInference/OpenTelemetry). FastAPI + uvicorn for the HTTP layer.

## Commands
```bash
uv sync                                      # install / update env
uv add <pkg>   /   uv add --dev <pkg>        # add dependency (updates pyproject + lock)
uvx arize-phoenix serve                      # Phoenix UI + collector on :6006 (keep it running)
uv run python scripts/check_setup.py         # verify .env, PayPal OAuth, Claude, Phoenix
uv run paypal-ai-hackathon "<prompt>"        # run the agent once from the CLI
uv run uvicorn paypal_ai_hackathon.api:app --reload   # API on :8000 (/docs)
uv run pytest -m "not live"                  # offline tests (run before every commit)
uv run ruff check --fix . && uv run ruff format .
```

## Layout
- `src/paypal_ai_hackathon/config.py`: every setting goes through `Settings` (pydantic-settings, reads `.env`). Don't use `os.getenv` elsewhere.
- `tracing.py`: call `setup_tracing()` once at process start, before creating any Anthropic client.
- `paypal_tools.py`: adapter from the toolkit's tool registry to Anthropic tool definitions, plus dispatch.
- `agent.py`: manual Claude tool-use loop. `api.py`: FastAPI app.
- `scripts/`: one-off and dev scripts. `tests/`: pytest; mark tests that hit real APIs with `@pytest.mark.live`.

## Gotchas (read before touching these areas)
- **Phoenix server must NOT be installed in the project env.** `arize-phoenix` conflicts with the toolkit's deps
  (graphql-core) and its `phoenix` package breaks `import phoenix.otel`. Always run it with `uvx`. The project
  only depends on `arize-phoenix-otel` + `openinference-instrumentation-anthropic`.
- **The PayPal toolkit has no Anthropic adapter.** We build tools from `paypal_agent_toolkit.shared.tools` and
  run them through `PayPalAPI.run`. Tool names in the installed Python package differ from the GitHub README
  (e.g. `get_order_details`, not `get_order`; no refund tools). Trust the registry, not the README.
- The toolkit is **synchronous** (`requests`) and fetches a new OAuth token on every call. Wrap it in
  `asyncio.to_thread` inside async code, and cache tokens if you write your own PayPal client.
- **Don't set the toolkit's logger to DEBUG** in anything shared or recorded: it logs request headers, including the Bearer token.
- `anthropic` 1.x is built on `httpx2`. Don't pass `httpx` objects (clients, timeouts) to the Anthropic client.
- Opus 5.5 API rules: thinking is always on (never send `thinking: disabled` or `budget_tokens`), forced
  `tool_choice` (`any`/`tool`) returns 400, and there's no assistant prefill. Control depth with
  `output_config.effort`. Append `response.content` unchanged to history and never edit earlier turns.
  Return all `tool_result`s for one turn in a single user message.
- Agent calls use `client.beta.messages.create` with `fallbacks="default"` (beta `server-side-fallback-2026-07-01`)
  so a refused turn is rerouted. Always check `stop_reason` (`refusal`, `max_tokens`) before using content.
- PayPal sandbox: buyer approval happens in the browser via the order's `approve` link before
  `pay_order`/capture works. Use the sandbox personal account from the developer dashboard for the demo.

## Rules
- **Secrets live only in `.env`** (gitignored). Add every new variable to `.env.example` with an empty value
  and a comment. Never print, log, or commit keys or tokens.
- **Sandbox only.** Never point `PAYPAL_ENVIRONMENT` at PRODUCTION or handle real money or card data.
- Any agent action that moves money or emails a customer needs an explicit confirmation step in the UX.
  It's safer, and judges reward it.
- Every new LLM or PayPal step gets a span (`get_tracer().start_as_current_span`) so the run shows up in Phoenix.
  Use Phoenix traces to debug agent behaviour before changing prompts.
- Keep functions small and typed; use pydantic models at the edges (API, tool inputs). Match the existing style;
  ruff config is in `pyproject.toml`.
- Commit small and often with imperative messages. Run offline tests and ruff before committing. Work on `main` unless told otherwise.

## Submission checklist (keep this current)
- [ ] Public GitHub repo with LICENSE (MIT) visible in About
- [ ] README: problem, who it's for, architecture, exact setup/run steps for judges (or a hosted URL, e.g. Render)
- [ ] Devpost text: features, and which AI tools are used and how
- [ ] Demo video < 3 min on YouTube (public), showing the end-to-end flow working, with no copyrighted music
- [ ] Optional sponsor prizes considered (AG Grid, APIMatic, Render, Channel3, Bryntum, ...)
