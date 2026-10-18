# PayPal AI Hackathon

Entry for "Build What's Next with PayPal and AI" (Devpost). **Deadline: Thu 12 Nov 2026, 12:00 PT.**
Hard requirement: the project must *meaningfully* use both PayPal (sandbox) and AI. Judged on technical
implementation, design (a complete product, not a PoC), impact, innovation, and a demo video under 3 minutes.

**Status: ideation.** The product idea isn't chosen yet. Don't build product features until it is; keep
`src/` as a thin, working skeleton until then.

## Stack
- Python 3.13, managed **only** with `uv`. Never `pip install` and never edit `uv.lock` by hand.
- AI via the official `openai` SDK, Chat Completions with function calling. Models: `gpt-4o-mini` by default
  (`OPENAI_MODEL`), `gpt-4o` for harder steps (`OPENAI_MODEL_SMART`). Both are on the user's free daily-token
  tier. **Don't switch to other or paid models without asking.**
- PayPal via `paypal-agent-toolkit` (sandbox), plus raw REST calls with `httpx` when the toolkit lacks an endpoint.
- Tracing via Arize Phoenix (OpenInference/OpenTelemetry). FastAPI + uvicorn for the HTTP layer.

## Commands
```bash
uv sync                                      # install / update env
uv add <pkg>   /   uv add --dev <pkg>        # add dependency (updates pyproject + lock)
uvx arize-phoenix serve                      # Phoenix UI + collector on :6006 (keep it running)
uv run python scripts/check_setup.py         # verify .env, PayPal OAuth, OpenAI, Phoenix
uv run paypal-ai-hackathon "<prompt>"        # run the agent once from the CLI
uv run uvicorn paypal_ai_hackathon.api:app --reload   # API on :8000 (/docs)
uv run pytest -m "not live"                  # offline tests (run before every commit)
uv run ruff check --fix . && uv run ruff format .
```

## Layout
- `src/paypal_ai_hackathon/config.py`: every setting goes through `Settings` (pydantic-settings, reads `.env`). Don't use `os.getenv` elsewhere.
- `tracing.py`: call `setup_tracing()` once at process start, before creating any OpenAI client.
- `paypal_tools.py`: adapter from the toolkit's tool registry to OpenAI function tools, plus dispatch.
- `agent.py`: manual tool-calling loop; get clients from `openai_client()`. `api.py`: FastAPI app.
- `scripts/`: one-off and dev scripts. `tests/`: pytest; mark tests that hit real APIs with `@pytest.mark.live`.

## Gotchas (read before touching these areas)
- **Phoenix server must NOT be installed in the project env.** `arize-phoenix` conflicts with the toolkit's deps
  (graphql-core) and its `phoenix` package breaks `import phoenix.otel`. Always run it with `uvx`. The project
  only depends on `arize-phoenix-otel` + `openinference-instrumentation-openai`.
- **Don't use the toolkit's own OpenAI adapter** (`paypal_agent_toolkit.openai`). It's built on `openai-agents`
  0.0.2, which is ancient. We build tools from `paypal_agent_toolkit.shared.tools` and run them through `PayPalAPI.run`. Tool names in the installed Python package differ from the GitHub README
  (e.g. `get_order_details`, not `get_order`; no refund tools). Trust the registry, not the README.
- The toolkit is **synchronous** (`requests`) and fetches a new OAuth token on every call. Wrap it in
  `asyncio.to_thread` inside async code, and cache tokens if you write your own PayPal client.
- **Don't set the toolkit's logger to DEBUG** in anything shared or recorded: it logs request headers, including the Bearer token.
- **`openai` is stuck below 2.0** because the toolkit pulls in old CrewAI/LangChain packages. So
  `openinference-instrumentation-openai` is pinned to `<0.1.60` (0.1.60+ needs openai 2.8 and silently traces
  nothing). Don't bump either one unless you drop the toolkit dependency.
- **The OpenAI SDK doesn't read `.env`**, only `os.environ`. Always create clients via `agent.openai_client()`,
  which takes the key from `Settings`. A bare `OpenAI()` fails with "api_key must be set".
- Chat Completions tool loop: append the assistant message (with its `tool_calls`), then exactly one
  `{"role": "tool", "tool_call_id": ...}` message per call, or the next request 400s.
  `function.arguments` is a JSON string, so parse it with `json.loads`.
- gpt-4o-mini sometimes invents tool arguments, such as fake emails or currencies. Validate money amounts and
  recipients before calling PayPal, and use gpt-4o where accuracy matters.
- PayPal sandbox: buyer approval happens in the browser via the order's `approve` link before
  `pay_order`/capture works. Use the sandbox personal account from the developer dashboard for the demo.

## Rules
- **Model split:** the main session (Opus) plans, designs and reviews. Delegate well-specified implementation
  work to the `coder` subagent (Sonnet, `.claude/agents/coder.md`) with a brief that names the files and what
  done looks like. Keep tiny edits (a few lines) in the main session, because a subagent starts cold and re-reads context.
  Review the coder's diff before committing.
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
