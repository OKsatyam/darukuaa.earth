"""
Optional LLM narration layer — Groq (OpenAI-compatible API, free tier for
open models like Llama). This is the ONLY place an LLM touches this system,
and its job is deliberately narrow: rephrase an already-decided, already
source-cited explanation into more natural conversational prose. It never
picks the reasoning chain, never adds a fact, magnitude or source that isn't
already in the deterministic text handed to it — connections.json + the
guardrails remain the sole source of truth for WHAT is said; this only
changes HOW it's said.

Deliberately fault-tolerant, same philosophy as rag.py: no API key, a
network hiccup, a timeout, or a malformed response should all just fall back
to the deterministic template — the chat should never look "broken" for a
reason this optional layer caused. The structured `recommendation.explanation`
field in the API response is ALWAYS the deterministic, source-grounded text
regardless of narration — only the conversational `reply_text` bubble is
ever replaced, so the auditable evidence trail never depends on an LLM call
succeeding.
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger("darukaa.narration")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"
TIMEOUT_SECONDS = 6.0

SYSTEM_PROMPT = (
    "You rephrase an already-verified ecological reasoning explanation into "
    "clear, natural, conversational language for a farmer or land manager in "
    "India. Rules: (1) Do not add any fact, number, mechanism, or source that "
    "is not already present in the text you're given. (2) Keep every cited "
    "magnitude, percentage, and source name exactly as given — do not round, "
    "invent, or drop them. (3) Do not add hedging or disclaimers beyond what's "
    "given. (4) Keep it to 2-4 sentences. (5) Output only the rephrased text, "
    "nothing else."
)


def narrate(deterministic_text: str) -> str | None:
    """
    Returns a rephrased version of deterministic_text, or None if narration
    isn't configured or fails for any reason (caller should fall back to
    deterministic_text itself in that case — never block on this).
    """
    if not settings.groq_api_key:
        return None

    try:
        response = httpx.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": deterministic_text},
                ],
                "temperature": 0.3,
                "max_tokens": 300,
            },
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        return text or None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Narration skipped/failed: %s", exc)
        return None
