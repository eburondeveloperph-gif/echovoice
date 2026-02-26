from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    ts: str
    version: str


class MetaFeatures(BaseModel):
    voice_cloning: bool = True
    streaming: bool = True
    realtime: bool = True


class MetaResponse(BaseModel):
    brand: str = "EchoLabs by Eburon AI"
    models: list[str]
    features: MetaFeatures


LatencyMode = Literal["balanced", "low", "ultra_low"]
AudioFormat = Literal["wav", "mp3"]


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    voice_id: str | None = None
    format: AudioFormat = "wav"
    latency_mode: LatencyMode = "balanced"
    nuance: float = Field(default=0.8, ge=0.0, le=1.0)


class TTSResponse(BaseModel):
    audio_url: str
    duration_ms: int
    meta: dict[str, Any]


class STTResponse(BaseModel):
    transcript: str
    words: list[dict[str, Any]] = Field(default_factory=list)
    meta: dict[str, Any]


class VoiceCloneResponse(BaseModel):
    voice_id: str
    status: str


class VoiceRecord(BaseModel):
    voice_id: str
    name: str
    status: str = "ready"
    created_at: str
    updated_at: str
    sample_files: list[str] = Field(default_factory=list)


class VoiceListResponse(BaseModel):
    voices: list[VoiceRecord]


class VoicePreviewResponse(BaseModel):
    voice_id: str
    preview_text: str
    audio_url: str
    duration_ms: int


class VoiceSyncResponse(BaseModel):
    synced: int
    voices: list[VoiceRecord]


class AdminConfigResponse(BaseModel):
    Sugar: str
    Salt: str
    Lime: str
    Pepper: bool
    Mint: str
    Cocoa: str
    Vanilla: str
    Ice: str


class AdminConfigUpdate(BaseModel):
    Sugar: str | None = None
    Salt: str | None = None
    Lime: str | None = None
    Pepper: bool | None = None
    Mint: str | None = None
    Cocoa: str | None = None
    Vanilla: str | None = None
    Ice: str | None = None


class ConvoTurnRequest(BaseModel):
    session_id: str | None = None
    voice_id: str | None = None
    text: str = Field(min_length=1, max_length=5000)
    latency_mode: LatencyMode = "balanced"
    nuance: float = Field(default=0.9, ge=0.0, le=1.0)
    agent_prompt: str | None = Field(default=None, max_length=2000)


class ConvoTurnResponse(BaseModel):
    session_id: str
    user_text: str
    agent_text: str
    audio_url: str
    duration_ms: int
    meta: dict[str, Any]
