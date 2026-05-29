"""Decision logging and lightweight token monitoring for the chatbot."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


LOG_DIR = Path("logs")
GUARDRAIL_LOG_PATH = LOG_DIR / "guardrail_decisions.csv"
TOKEN_LOG_PATH = LOG_DIR / "token_usage.csv"


@dataclass(frozen=True)
class TokenUsage:
    """Token usage returned by the chat API, when available."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_prompt_tokens: int | None = None


def estimate_text_tokens(text: str) -> int:
    """Approximate token count using a simple character-based estimate.

    This is not exact, but it is useful for detecting very large prompts before
    sending them to the API. A common rough estimate is about four characters
    per token for English text.
    """

    if not text:
        return 0
    return max(1, len(text) // 4)


def estimate_message_tokens(messages: list[dict[str, str]]) -> int:
    """Estimate token usage for a list of chat messages."""

    estimated = 2  # small overhead for the chat request
    for message in messages:
        estimated += 4  # rough per-message overhead
        estimated += estimate_text_tokens(message.get("role", ""))
        estimated += estimate_text_tokens(message.get("content", ""))
    return estimated


def log_guardrail_decision(
    *,
    stage: str,
    allowed: bool,
    reason: str,
    user_input: str = "",
    similarity: float | None = None,
    estimated_tokens: int | None = None,
) -> None:
    """Write a guardrail decision to a CSV audit file."""

    _ensure_log_dir()
    file_exists = GUARDRAIL_LOG_PATH.exists()

    with GUARDRAIL_LOG_PATH.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "timestamp_utc",
                "stage",
                "allowed",
                "reason",
                "similarity",
                "estimated_tokens",
                "input_preview",
            ],
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp_utc": _timestamp(),
                "stage": stage,
                "allowed": allowed,
                "reason": reason,
                "similarity": "" if similarity is None else round(similarity, 4),
                "estimated_tokens": "" if estimated_tokens is None else estimated_tokens,
                "input_preview": user_input.replace("\n", " ")[:160],
            }
        )


def log_token_usage(*, estimated_prompt_tokens: int, usage: TokenUsage) -> None:
    """Write token usage information to a CSV audit file."""

    _ensure_log_dir()
    file_exists = TOKEN_LOG_PATH.exists()

    with TOKEN_LOG_PATH.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "timestamp_utc",
                "estimated_prompt_tokens",
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
            ],
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp_utc": _timestamp(),
                "estimated_prompt_tokens": estimated_prompt_tokens,
                "prompt_tokens": "" if usage.prompt_tokens is None else usage.prompt_tokens,
                "completion_tokens": "" if usage.completion_tokens is None else usage.completion_tokens,
                "total_tokens": "" if usage.total_tokens is None else usage.total_tokens,
            }
        )


def _ensure_log_dir() -> None:
    LOG_DIR.mkdir(exist_ok=True)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
