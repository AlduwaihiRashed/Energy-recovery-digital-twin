from __future__ import annotations

import os

import httpx

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
# gemma4:e4b confirmed (via `ollama show`) to support native tool-calling + 131k
# context. Swappable via env var -- e2b is not meaningfully faster in practice
# (both are dominated by reasoning-trace generation, see copilot spike notes),
# so e4b is kept as the default for better tool-calling reliability.
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:e4b")


class OllamaClient:
    """Thin wrapper around Ollama's /api/chat with native tool-calling.
    think=False roughly halves round-1 latency (~22s -> ~13s in spike
    testing) since the tool-trace UI already gives the user visibility into
    what the model did, so the chain-of-thought isn't needed."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = DEFAULT_MODEL, timeout_s: float = 90.0):
        self.base_url = base_url
        self.model = model
        self.timeout_s = timeout_s

    async def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            resp = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "tools": tools or [],
                    "stream": False,
                    "think": False,
                    "options": {"temperature": 0.2},
                },
            )
            resp.raise_for_status()
            return resp.json()
