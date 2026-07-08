from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.copilot.loop import run_copilot_turn
from app.copilot.ollama_client import OllamaClient

router = APIRouter(prefix="/api/copilot", tags=["copilot"])

_client = OllamaClient()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    db = request.app.state.db
    history = [m.model_dump() for m in body.history]
    return await run_copilot_turn(db, _client, body.message, history)
