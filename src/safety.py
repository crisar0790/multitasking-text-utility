import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import BASE_DIR


DEFAULT_SAFETY_LOG_PATH = BASE_DIR / "metrics" / "safety_events.jsonl"

MANIPULATION_PATTERNS = (
    # Spanish
    "ignora las instrucciones",
    "ignora todas las instrucciones",
    "ignora las instrucciones anteriores",
    "olvida tus reglas",
    "olvida tu tarea",
    "prompt de sistema",
    "modo desarrollador",
    "sin restricciones",

    # English
    "ignore previous instructions",
    "ignore all previous",
    "ignore the previous instructions",
    "disregard previous instructions",
    "forget your rules",
    "system override",
    "system prompt",
    "developer mode",
    "without restrictions",
)

# These patterns are heuristic and do not cover all sensitive data.
SENSITIVE_DATA_PATTERNS = (
    (
        r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        "[CARD_NUMBER]",
    ),
    (
        r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b",
        "[EMAIL]",
    ),
    (
        r"\b(?:sk-|gsk_|AIza)[A-Za-z0-9_-]{10,}\b",
        "[API_KEY]",
    ),
)


def detect_manipulation(text: str) -> list[str]:
    """
    Return recognized suspicious phrases, not a safety verdict.
    """
    normalized_text = text.casefold()

    return [
        pattern
        for pattern in MANIPULATION_PATTERNS
        if pattern in normalized_text
    ]


def redact_sensitive_data(text: str) -> tuple[str, int]:
    """
    Replace recognized sensitive data and count replacements.
    """
    total_replacements = 0

    for pattern, replacement in SENSITIVE_DATA_PATTERNS:
        text, replacements = re.subn(pattern, replacement, text)
        total_replacements += replacements

    return text, total_replacements


def analyze_input(text: str) -> dict[str, Any]:
    """
    Analyze and redact input without automatically blocking it.
    """
    manipulation_patterns = detect_manipulation(text)
    clean_text, redacted_count = redact_sensitive_data(text)

    return {
        "clean_text": clean_text,
        "manipulation_patterns": manipulation_patterns,
        "redacted_count": redacted_count,
    }


def create_safety_fallback() -> dict[str, Any]:
    """
    Return a safe response that follows the JSON contract.
    """
    return {
        "answer": (
            "I cannot assist with this request. "
            "Please contact a support agent for guidance."
        ),
        "confidence": 0.0,
        "actions": ["escalate_to_human"],
        "topics": ["other"],
        "requires_human_attention": True,
    }


def log_safety_event(
    event_type: str,
    decision: str,
    response_id: str | None = None,
    manipulation_patterns: list[str] | None = None,
    redacted_count: int = 0,
    file_path: Path = DEFAULT_SAFETY_LOG_PATH,
    redacted_query: str | None = None,
) -> None:
    """Record safety metadata and an optional redacted query."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "decision": decision,
        "response_id": response_id,
        "manipulation_patterns": manipulation_patterns or [],
        "redacted_count": redacted_count,
    }

    if redacted_query is not None:
        event["redacted_query"] = redacted_query

    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")