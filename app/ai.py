import json
import logging
from functools import lru_cache
from typing import Any

from openai import OpenAI

from app.config import get_settings
from app.prompts import FALLBACK_REPLY, MEMORY_EXTRACTION_PROMPT, SYSTEM_PROMPT, format_memory
from app.schemas import MemorySaved

logger = logging.getLogger(__name__)


@lru_cache
def get_openai_client() -> OpenAI | None:
    settings = get_settings()
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def extract_memories(message: str) -> list[MemorySaved]:
    client = get_openai_client()
    if client is None:
        return []

    settings = get_settings()
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": MEMORY_EXTRACTION_PROMPT},
                {"role": "user", "content": message},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content or '{"memories":[]}'
        parsed = json.loads(content)
        return _parse_memories(parsed)
    except Exception:
        logger.exception("Memory extraction failed")
        return []


def generate_reply(
    sender_id: str,
    message: str,
    recent_chat: list[dict[str, str]],
    memory: dict[str, str],
) -> str:
    client = get_openai_client()
    if client is None:
        return FALLBACK_REPLY

    settings = get_settings()
    context = (
        f"Messenger sender_id: {sender_id}\n\n"
        f"Saved family memory:\n{format_memory(memory)}"
    )

    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": context},
    ]
    messages.extend(_chat_history_messages(recent_chat))
    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=0.4,
        )
        reply = (response.choices[0].message.content or "").strip()
        return reply or FALLBACK_REPLY
    except Exception:
        logger.exception("Reply generation failed")
        return FALLBACK_REPLY


def _parse_memories(parsed: Any) -> list[MemorySaved]:
    raw_memories = parsed.get("memories", []) if isinstance(parsed, dict) else []
    if not isinstance(raw_memories, list):
        return []

    memories: list[MemorySaved] = []
    for item in raw_memories:
        if not isinstance(item, dict):
            continue
        key = _clean_memory_text(item.get("memory_key", ""), max_length=80)
        value = _clean_memory_text(item.get("memory_value", ""), max_length=500)
        if key and value:
            memories.append(MemorySaved(memory_key=key, memory_value=value))
    return memories[:10]


def _clean_memory_text(value: Any, max_length: int) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_length]


def _chat_history_messages(recent_chat: list[dict[str, str]]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for row in recent_chat:
        role = row.get("role")
        if role not in {"user", "assistant"}:
            continue
        content = row.get("message", "").strip()
        if content:
            messages.append({"role": role, "content": content})
    return messages[-20:]
