from __future__ import annotations

import json
import logging

from app.copilot.ollama_client import OllamaClient
from app.copilot.prompts import build_system_prompt
from app.copilot.tools import TOOL_SCHEMAS, execute_tool_safely
from app.historian.db import Database

logger = logging.getLogger("copilot.loop")

MAX_TOOL_ROUNDS = 4


async def run_copilot_turn(
    db: Database, client: OllamaClient, user_message: str, history: list[dict] | None = None
) -> dict:
    """Bounded tool-call loop: low temperature + think=False (set in
    OllamaClient), a hard round cap, and manual arg validation inside each
    tool (see execute_tool_safely) so a malformed call feeds an {"error": ...}
    back to the model instead of crashing the chat."""
    messages: list[dict] = [{"role": "system", "content": build_system_prompt()}]
    messages.extend(history or [])
    messages.append({"role": "user", "content": user_message})

    tool_trace: list[dict] = []

    for round_num in range(MAX_TOOL_ROUNDS):
        response = await client.chat(messages, tools=TOOL_SCHEMAS)
        message = response.get("message", {})
        messages.append(message)

        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            return {"reply": message.get("content", ""), "tool_trace": tool_trace}

        logger.info("copilot round=%d tool_calls=%d", round_num, len(tool_calls))
        for call in tool_calls:
            fn = call.get("function", {})
            name = fn.get("name", "")
            args = fn.get("arguments", {}) or {}
            result = await execute_tool_safely(db, name, args)
            tool_trace.append({"name": name, "args": args, "result": result})
            messages.append({"role": "tool", "name": name, "content": json.dumps(result)})

    # Exceeded MAX_TOOL_ROUNDS -- force a final non-tool answer so the chat
    # never hangs on a model that keeps calling tools.
    final = await client.chat(messages, tools=None)
    return {
        "reply": final.get("message", {}).get("content", "(unable to complete tool lookups)"),
        "tool_trace": tool_trace,
    }
