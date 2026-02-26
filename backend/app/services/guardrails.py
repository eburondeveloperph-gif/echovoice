from __future__ import annotations

import re
from typing import Any

_VENDOR_PATTERNS = [
    re.compile(r"eleven", re.IGNORECASE),
    re.compile(r"11\s*labs", re.IGNORECASE),
    re.compile(r"elevenlabs", re.IGNORECASE),
    re.compile(r"turbo\s*v?2\.5", re.IGNORECASE),
    re.compile(r"api\.elevenlabs", re.IGNORECASE),
]


def contains_vendor_string(value: str) -> bool:
    return any(pattern.search(value) for pattern in _VENDOR_PATTERNS)


def sanitize_text(value: str) -> str:
    redacted = value
    for pattern in _VENDOR_PATTERNS:
        redacted = pattern.sub("EchoLabs", redacted)
    return redacted


def sanitize_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: sanitize_payload(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [sanitize_payload(item) for item in payload]
    if isinstance(payload, tuple):
        return tuple(sanitize_payload(item) for item in payload)
    if isinstance(payload, str):
        return sanitize_text(payload)
    return payload


def provider_identity_message() -> str:
    return (
        "EchoLabs by Eburon AI operates through integrated internal infrastructure. "
        "Provider details are not disclosed in this interface."
    )


def is_provider_identity_question(text: str) -> bool:
    value = text.lower()
    return (
        "provider" in value
        or "vendor" in value
        or "what model" in value
        or "what api" in value
        or "which company" in value
    )


def safe_error_message(_: str | None = None) -> str:
    return "EchoLabs could not complete the request at this time. Please retry."
