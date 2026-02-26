from __future__ import annotations

import re
from typing import Any

import httpx

from app.core.config import Settings


class TTSTextEditor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: httpx.AsyncClient | None = None

    def _lazy_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.settings.ollama_timeout_seconds)
        return self._client

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        content = text.strip()
        if content.startswith("```"):
            content = re.sub(r"^```[a-zA-Z0-9_-]*", "", content).strip()
            content = re.sub(r"```$", "", content).strip()
        return content

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[a-zA-Z0-9']+", text.lower())

    def _similar_enough(self, original: str, edited: str) -> bool:
        original_tokens = self._tokenize(original)
        edited_tokens = self._tokenize(edited)
        if not original_tokens:
            return True
        if not edited_tokens:
            return False

        overlap = sum(1 for token in original_tokens if token in set(edited_tokens))
        ratio = overlap / max(1, len(original_tokens))
        return ratio >= self.settings.ollama_min_similarity_ratio

    @staticmethod
    def _insert_greeting_comma(text: str) -> str:
        # Example: "Hello how are you" -> "Hello, how are you"
        return re.sub(r"^(hello|hi|hey)\s+", lambda m: f"{m.group(1).capitalize()}, ", text, flags=re.IGNORECASE)

    @staticmethod
    def _ensure_terminal_punctuation(text: str) -> str:
        if not text:
            return text
        if text[-1] in ".!?":
            return text
        lowered = text.lower().strip()
        question_starts = ("who", "what", "when", "where", "why", "how", "can", "could", "would", "should", "is", "are")
        return text + ("?" if lowered.startswith(question_starts) else ".")

    def _light_edit(self, text: str) -> str:
        normalized = re.sub(r"\s+", " ", text).strip()
        normalized = self._insert_greeting_comma(normalized)
        if normalized:
            normalized = normalized[0].upper() + normalized[1:]
        normalized = self._ensure_terminal_punctuation(normalized)
        return normalized

    @staticmethod
    def _strip_ssml_tags(text: str) -> str:
        return re.sub(r"</?[^>]+>", "", text).strip()

    def _finalize_output(self, original: str, candidate: str) -> str:
        cleaned = self._strip_code_fences(candidate)
        cleaned = cleaned.strip()

        if not cleaned:
            return self._light_edit(original)

        if not self._similar_enough(original, cleaned):
            return self._light_edit(original)

        if self.settings.ollama_editor_ssml:
            if "<speak" not in cleaned:
                # Wrap lightly edited plain text as SSML.
                plain = self._light_edit(cleaned)
                return (
                    "<speak>"
                    f"<prosody rate='medium' pitch='+1st' volume='medium'>{plain}</prosody>"
                    "</speak>"
                )
            return cleaned

        return self._light_edit(self._strip_ssml_tags(cleaned))

    async def enhance_for_tts(self, text: str) -> str:
        base = text.strip()
        if not base:
            return base

        if not self.settings.tts_editor_enabled:
            return self._light_edit(base)

        word_count = len(self._tokenize(base))
        if word_count <= self.settings.ollama_short_text_words:
            return self._light_edit(base)

        try:
            client = self._lazy_client()
            system_prompt = (
                "You are an invisible TTS text editor. Preserve the same wording and order. "
                "Only improve punctuation, capitalization, pauses, and speaking rhythm. "
                "Do not add or remove meaning."
            )
            output_format = "SSML" if self.settings.ollama_editor_ssml else "plain text"
            prompt = (
                f"{system_prompt}\n"
                f"Output format: {output_format}.\n"
                "Return only edited text, no explanations.\n"
                f"Input:\n{base}"
            )

            response = await client.post(
                f"{self.settings.ollama_base_url.rstrip('/')}/api/generate",
                json={
                    "model": self.settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_predict": 256,
                    },
                },
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            candidate = str(payload.get("response", ""))
            return self._finalize_output(base, candidate)
        except Exception:
            return self._light_edit(base)
