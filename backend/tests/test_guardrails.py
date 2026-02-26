from app.services.guardrails import (
    contains_vendor_string,
    is_provider_identity_question,
    provider_identity_message,
    sanitize_payload,
)


def test_guardrails_redact_vendor_tokens() -> None:
    payload = {"message": "Powered by ElevenLabs with turbo v2.5"}
    sanitized = sanitize_payload(payload)
    assert "ElevenLabs" not in sanitized["message"]


def test_guardrails_detect_provider_queries() -> None:
    assert is_provider_identity_question("what provider powers this?")
    assert "Provider details" in provider_identity_message()


def test_guardrails_contains_vendor_string() -> None:
    assert contains_vendor_string("eleven")
    assert not contains_vendor_string("EchoLabs by Eburon AI")
