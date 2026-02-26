from __future__ import annotations

import mimetypes
import re
import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
from fastapi import HTTPException

from app.core.config import Settings
from app.services.alias_models import enforce_nuance, map_latency_mode, resolve_alias_config
from app.services.audio_utils import estimate_duration_ms, synth_demo_wav


class ProviderClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.alias = resolve_alias_config(settings)

    @property
    def _provider_ready(self) -> bool:
        return bool(self.settings.echolabs_sugar) and not self.settings.echolabs_demo_mode

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "xi-api-key": self.settings.echolabs_sugar,
            "accept": "application/json",
        }

    @staticmethod
    def _strip_ssml(text: str) -> str:
        return re.sub(r"</?[^>]+>", "", text).strip()

    async def tts(
        self,
        text: str,
        voice_id: str | None,
        fmt: str,
        latency_mode: str,
        nuance: float,
    ) -> tuple[bytes, str, int]:
        if not self._provider_ready:
            wav = synth_demo_wav(text)
            return wav, "wav", estimate_duration_ms(wav, "wav")

        provider_voice_id = voice_id or self.settings.default_voice_provider_id
        url = f"{self.settings.echolabs_salt.rstrip('/')}/v1/text-to-speech/{provider_voice_id}"
        output_format = "mp3_44100_128" if fmt == "mp3" else "pcm_44100"

        def build_payload(render_text: str) -> dict[str, Any]:
            return {
                "text": render_text,
                "model_id": self.alias.tts_provider_model,
                "voice_settings": {
                    "stability": 0.45,
                    "similarity_boost": 0.82,
                    "style": enforce_nuance(nuance),
                    "use_speaker_boost": True,
                },
                "output_format": output_format,
            }

        params = {"optimize_streaming_latency": map_latency_mode(latency_mode)}

        async def send_tts(render_text: str) -> bytes:
            async with httpx.AsyncClient(timeout=self.settings.provider_timeout_seconds) as client:
                response = await client.post(
                    url,
                    headers={
                        "xi-api-key": self.settings.echolabs_sugar,
                        "accept": "audio/mpeg" if fmt == "mp3" else "audio/wav",
                        "content-type": "application/json",
                    },
                    params=params,
                    json=build_payload(render_text),
                )
                response.raise_for_status()
                return response.content

        try:
            audio_bytes = await send_tts(text)
        except Exception:
            # If SSML formatting is rejected upstream, retry once with plain text.
            plain_text = self._strip_ssml(text)
            if plain_text and plain_text != text:
                try:
                    audio_bytes = await send_tts(plain_text)
                except Exception as exc:
                    raise HTTPException(
                        status_code=502,
                        detail={
                            "code": "ECHO_PROVIDER_TTS_FAILED",
                            "message": "EchoLabs audio generation failed.",
                        },
                    ) from exc
            else:
                raise HTTPException(
                    status_code=502,
                    detail={
                        "code": "ECHO_PROVIDER_TTS_FAILED",
                        "message": "EchoLabs audio generation failed.",
                    },
                )

        actual_format = "mp3" if fmt == "mp3" else "wav"
        return audio_bytes, actual_format, estimate_duration_ms(audio_bytes, actual_format)

    async def stt_from_file(
        self,
        file_path: Path,
        language: str | None = None,
        diarization: bool = False,
    ) -> dict[str, Any]:
        if not self._provider_ready:
            return {
                "transcript": f"Demo transcript for {file_path.name}",
                "words": [],
            }

        url = f"{self.settings.echolabs_salt.rstrip('/')}/v1/speech-to-text"
        mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        files = {
            "file": (file_path.name, file_path.read_bytes(), mime_type),
        }
        data = {
            "model_id": self.alias.stt_provider_model,
            "diarize": str(bool(diarization)).lower(),
        }
        if language:
            data["language_code"] = language

        try:
            async with httpx.AsyncClient(timeout=self.settings.provider_timeout_seconds) as client:
                response = await client.post(url, headers=self._headers, data=data, files=files)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "ECHO_PROVIDER_STT_FAILED",
                    "message": "EchoLabs transcription failed.",
                },
            ) from exc

        transcript = payload.get("text") or payload.get("transcript") or ""
        words = payload.get("words") or []
        return {"transcript": transcript, "words": words}

    async def stt_from_bytes(
        self,
        audio_bytes: bytes,
        suffix: str = ".webm",
        language: str | None = None,
        diarization: bool = False,
    ) -> dict[str, Any]:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            return await self.stt_from_file(Path(tmp.name), language=language, diarization=diarization)

    async def clone_voice(self, name: str, sample_paths: list[Path]) -> dict[str, str]:
        if not self._provider_ready:
            return {
                "provider_voice_id": f"demo_{uuid4().hex[:12]}",
                "status": "ready",
            }

        url = f"{self.settings.echolabs_salt.rstrip('/')}/v1/voices/add"
        files: list[tuple[str, tuple[str, bytes, str]]] = []
        for path in sample_paths:
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            files.append(("files", (path.name, path.read_bytes(), mime)))

        try:
            async with httpx.AsyncClient(timeout=self.settings.provider_timeout_seconds) as client:
                response = await client.post(
                    url,
                    headers={"xi-api-key": self.settings.echolabs_sugar},
                    data={"name": name},
                    files=files,
                )
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "ECHO_PROVIDER_CLONE_FAILED",
                    "message": "EchoLabs voice profile creation failed.",
                },
            ) from exc

        provider_voice_id = payload.get("voice_id") or payload.get("id") or f"voice_{uuid4().hex}"
        return {"provider_voice_id": provider_voice_id, "status": "ready"}

    async def list_provider_voices(self) -> list[dict[str, str]]:
        if not self._provider_ready:
            return []

        url = f"{self.settings.echolabs_salt.rstrip('/')}/v1/voices"
        try:
            async with httpx.AsyncClient(timeout=self.settings.provider_timeout_seconds) as client:
                response = await client.get(url, headers=self._headers)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return []

        voices = payload.get("voices") or []
        results: list[dict[str, str]] = []
        for voice in voices:
            results.append(
                {
                    "provider_voice_id": voice.get("voice_id", ""),
                    "name": voice.get("name", "Voice"),
                }
            )
        return results

    async def delete_provider_voice(self, provider_voice_id: str) -> None:
        if not self._provider_ready or not provider_voice_id:
            return
        url = f"{self.settings.echolabs_salt.rstrip('/')}/v1/voices/{provider_voice_id}"
        try:
            async with httpx.AsyncClient(timeout=self.settings.provider_timeout_seconds) as client:
                response = await client.delete(url, headers=self._headers)
                response.raise_for_status()
        except Exception:
            return
