from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings


PUBLIC_ALIASES = ["echo-tts@v2.5", "echo-stt@v2", "echo-realtime@v1"]


@dataclass(slots=True)
class AliasModelConfig:
    tts_alias: str
    stt_alias: str
    realtime_alias: str
    tts_provider_model: str
    stt_provider_model: str
    realtime_provider_mode: str
    high_nuance: bool


def public_alias_models() -> list[str]:
    return PUBLIC_ALIASES.copy()


def resolve_alias_config(settings: Settings) -> AliasModelConfig:
    return AliasModelConfig(
        tts_alias="echo-tts@v2.5",
        stt_alias="echo-stt@v2",
        realtime_alias="echo-realtime@v1",
        tts_provider_model=settings.provider_tts_model_id,
        stt_provider_model=settings.provider_stt_model_id,
        realtime_provider_mode=settings.provider_realtime_mode_id,
        high_nuance=True if settings.echolabs_pepper else True,
    )


def map_latency_mode(mode: str) -> int:
    mapping = {
        "balanced": 2,
        "low": 3,
        "ultra_low": 4,
    }
    return mapping.get(mode, 2)


def enforce_nuance(value: float) -> float:
    # High nuance is enforced server-side. Client slider is advisory.
    return max(0.7, min(1.0, value))
