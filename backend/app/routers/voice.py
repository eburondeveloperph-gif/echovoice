from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.models.schemas import (
    VoiceCloneResponse,
    VoiceListResponse,
    VoicePreviewResponse,
    VoiceRecord,
    VoiceSyncResponse,
)
from app.services.deps import get_provider_client, get_storage
from app.services.guardrails import sanitize_payload, sanitize_text
from app.services.provider_client import ProviderClient
from app.services.storage import StorageService

router = APIRouter(prefix="/v1/voice", tags=["voice"])

PREVIEW_TEXT = "HI THIS IS ECHO VOICE FROM EBURON AI"


def _normalize_echo_voice_name(name: str) -> str:
    clean = sanitize_text(name).strip() or "Echo Profile"
    if clean.lower().startswith("echo voice"):
        return clean
    return f"Echo Voice - {clean}"


def _stable_internal_voice_id(provider_voice_id: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9]", "", provider_voice_id.lower())
    suffix = safe[:24] if safe else uuid4().hex[:12]
    return f"echo_voice_ext_{suffix}"


async def _sync_provider_voices(storage: StorageService, provider: ProviderClient) -> int:
    synced = 0
    now = datetime.now(tz=timezone.utc).isoformat()
    provider_voices = await provider.list_provider_voices()

    for provider_voice in provider_voices:
        provider_voice_id = (provider_voice.get("provider_voice_id") or "").strip()
        if not provider_voice_id:
            continue

        existing = storage.get_voice_by_provider_id(provider_voice_id)
        name = _normalize_echo_voice_name(provider_voice.get("name") or "Echo Profile")

        if existing:
            existing["name"] = name
            existing["status"] = "ready"
            existing["updated_at"] = now
            existing.setdefault("sample_files", [])
            existing["source"] = "provider"
            storage.upsert_voice(existing)
            synced += 1
            continue

        record = {
            "voice_id": _stable_internal_voice_id(provider_voice_id),
            "name": name,
            "provider_voice_id": provider_voice_id,
            "status": "ready",
            "created_at": now,
            "updated_at": now,
            "sample_files": [],
            "source": "provider",
        }
        storage.upsert_voice(record)
        synced += 1

    return synced


@router.post("/clone", response_model=VoiceCloneResponse)
async def clone_voice(
    name: str = Form(...),
    samples: list[UploadFile] = File(...),
    storage: StorageService = Depends(get_storage),
    provider: ProviderClient = Depends(get_provider_client),
) -> VoiceCloneResponse:
    if len(samples) == 0:
        raise HTTPException(
            status_code=400,
            detail={"code": "ECHO_SAMPLES_REQUIRED", "message": "At least one sample is required."},
        )

    sample_relative_paths: list[str] = []
    sample_absolute_paths: list[Path] = []

    for sample in samples:
        relative_path = await storage.save_upload(sample, subdir="voice_samples")
        sample_relative_paths.append(relative_path)
        sample_absolute_paths.append(Path(storage.resolve_relative_path(relative_path)))

    provider_result = await provider.clone_voice(name=name, sample_paths=sample_absolute_paths)

    now = datetime.now(tz=timezone.utc).isoformat()
    internal_voice_id = f"echo_voice_{uuid4().hex[:12]}"
    record_payload = {
        "voice_id": internal_voice_id,
        "name": _normalize_echo_voice_name(name),
        "provider_voice_id": provider_result.get("provider_voice_id"),
        "status": provider_result.get("status", "ready"),
        "created_at": now,
        "updated_at": now,
        "sample_files": sample_relative_paths,
        "source": "clone",
    }
    storage.upsert_voice(record_payload)

    response = VoiceCloneResponse(voice_id=internal_voice_id, status=record_payload["status"])
    return VoiceCloneResponse(**sanitize_payload(response.model_dump()))


@router.post("/sync", response_model=VoiceSyncResponse)
async def sync_voices(
    storage: StorageService = Depends(get_storage),
    provider: ProviderClient = Depends(get_provider_client),
) -> VoiceSyncResponse:
    synced = await _sync_provider_voices(storage, provider)
    records = [VoiceRecord(**item) for item in storage.list_voices(include_deleted=False)]
    response = VoiceSyncResponse(synced=synced, voices=records)
    return VoiceSyncResponse(**sanitize_payload(response.model_dump()))


@router.get("/list", response_model=VoiceListResponse)
async def list_voices(
    storage: StorageService = Depends(get_storage),
    provider: ProviderClient = Depends(get_provider_client),
) -> VoiceListResponse:
    await _sync_provider_voices(storage, provider)
    records = [VoiceRecord(**item) for item in storage.list_voices(include_deleted=False)]
    response = VoiceListResponse(voices=records)
    return VoiceListResponse(**sanitize_payload(response.model_dump()))


@router.post("/preview/{voice_id}", response_model=VoicePreviewResponse)
async def preview_voice(
    voice_id: str,
    storage: StorageService = Depends(get_storage),
    provider: ProviderClient = Depends(get_provider_client),
) -> VoicePreviewResponse:
    voice = storage.get_voice(voice_id)
    if not voice or voice.get("status") == "deleted":
        raise HTTPException(
            status_code=404,
            detail={"code": "ECHO_VOICE_NOT_FOUND", "message": "Voice profile not found."},
        )

    provider_voice_id = voice.get("provider_voice_id") or provider.settings.default_voice_provider_id
    audio_bytes, _, duration_ms = await provider.tts(
        text=PREVIEW_TEXT,
        voice_id=provider_voice_id,
        fmt="wav",
        latency_mode="balanced",
        nuance=0.9,
    )
    relative = storage.save_bytes(audio_bytes, suffix=".wav", subdir="previews")

    response = VoicePreviewResponse(
        voice_id=voice_id,
        preview_text=PREVIEW_TEXT,
        audio_url=storage.file_url(relative),
        duration_ms=duration_ms,
    )
    return VoicePreviewResponse(**sanitize_payload(response.model_dump()))


@router.get("/{voice_id}", response_model=VoiceRecord)
async def get_voice(voice_id: str, storage: StorageService = Depends(get_storage)) -> VoiceRecord:
    voice = storage.get_voice(voice_id)
    if not voice or voice.get("status") == "deleted":
        raise HTTPException(
            status_code=404,
            detail={"code": "ECHO_VOICE_NOT_FOUND", "message": "Voice profile not found."},
        )
    return VoiceRecord(**sanitize_payload(voice))


@router.delete("/{voice_id}")
async def delete_voice(
    voice_id: str,
    storage: StorageService = Depends(get_storage),
    provider: ProviderClient = Depends(get_provider_client),
) -> dict[str, str]:
    voice = storage.get_voice(voice_id)
    if not voice or voice.get("status") == "deleted":
        raise HTTPException(
            status_code=404,
            detail={"code": "ECHO_VOICE_NOT_FOUND", "message": "Voice profile not found."},
        )

    provider_voice_id = voice.get("provider_voice_id")
    if provider_voice_id:
        await provider.delete_provider_voice(provider_voice_id)
    storage.soft_delete_voice(voice_id)
    return {"status": "deleted", "voice_id": voice_id}
