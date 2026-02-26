from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.models.schemas import STTResponse
from app.services.alias_models import resolve_alias_config
from app.services.deps import get_provider_client, get_storage
from app.services.guardrails import sanitize_payload
from app.services.provider_client import ProviderClient
from app.services.storage import StorageService

router = APIRouter(prefix="/v1", tags=["stt"])


@router.post("/stt", response_model=STTResponse)
async def stt(
    audio: UploadFile = File(...),
    language: str | None = Form(default=None),
    diarization: bool = Form(default=False),
    storage: StorageService = Depends(get_storage),
    provider: ProviderClient = Depends(get_provider_client),
) -> STTResponse:
    content_type = audio.content_type or "application/octet-stream"
    if not content_type.startswith("audio/"):
        raise HTTPException(
            status_code=400,
            detail={"code": "ECHO_INVALID_AUDIO", "message": "Only audio uploads are accepted."},
        )

    relative_path = await storage.save_upload(audio)
    absolute_path = storage.resolve_relative_path(relative_path)

    stt_payload = await provider.stt_from_file(Path(absolute_path), language=language, diarization=diarization)
    response = STTResponse(
        transcript=stt_payload.get("transcript", ""),
        words=stt_payload.get("words", []),
        meta={"model_alias": resolve_alias_config(provider.settings).stt_alias},
    )
    return STTResponse(**sanitize_payload(response.model_dump()))
