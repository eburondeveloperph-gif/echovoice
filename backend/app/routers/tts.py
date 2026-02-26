from __future__ import annotations

from fastapi import APIRouter, Depends

from app.models.schemas import TTSRequest, TTSResponse
from app.services.alias_models import resolve_alias_config
from app.services.deps import get_provider_client, get_storage, get_text_editor
from app.services.guardrails import is_provider_identity_question, provider_identity_message, sanitize_payload
from app.services.provider_client import ProviderClient
from app.services.storage import StorageService
from app.services.text_editor import TTSTextEditor

router = APIRouter(prefix="/v1", tags=["tts"])


@router.post("/tts", response_model=TTSResponse)
async def tts(
    body: TTSRequest,
    storage: StorageService = Depends(get_storage),
    provider: ProviderClient = Depends(get_provider_client),
    text_editor: TTSTextEditor = Depends(get_text_editor),
) -> TTSResponse:
    prompt = body.text
    if is_provider_identity_question(prompt):
        prompt = provider_identity_message()
    else:
        prompt = await text_editor.enhance_for_tts(prompt)

    effective_voice_id = body.voice_id
    if body.voice_id:
        voice_record = storage.get_voice(body.voice_id)
        if voice_record and voice_record.get("provider_voice_id"):
            effective_voice_id = str(voice_record.get("provider_voice_id"))

    audio_bytes, actual_format, duration_ms = await provider.tts(
        text=prompt,
        voice_id=effective_voice_id,
        fmt=body.format,
        latency_mode=body.latency_mode,
        nuance=body.nuance,
    )

    suffix = ".mp3" if actual_format == "mp3" else ".wav"
    relative_path = storage.save_bytes(audio_bytes, suffix=suffix)

    response = TTSResponse(
        audio_url=storage.file_url(relative_path),
        duration_ms=duration_ms,
        meta={"model_alias": resolve_alias_config(provider.settings).tts_alias},
    )
    return TTSResponse(**sanitize_payload(response.model_dump()))
