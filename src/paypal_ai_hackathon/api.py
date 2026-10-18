"""FastAPI entry point. Run: uv run uvicorn paypal_ai_hackathon.api:app --reload"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from paypal_ai_hackathon.agent import AgentResult, run_agent
from paypal_ai_hackathon.config import get_settings
from paypal_ai_hackathon.tracing import setup_tracing


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_tracing()
    yield


app = FastAPI(title="PayPal AI Hackathon", lifespan=lifespan)


class AgentRequest(BaseModel):
    prompt: str


@app.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "model": settings.claude_model, "paypal": settings.paypal_environment}


@app.post("/agent")
async def agent(req: AgentRequest) -> AgentResult:
    # The agent loop and PayPal toolkit are blocking; keep them off the event loop.
    return await asyncio.to_thread(run_agent, req.prompt)
