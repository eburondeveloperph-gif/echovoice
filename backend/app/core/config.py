from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except Exception:
    from pydantic import BaseModel

    def SettingsConfigDict(**kwargs: Any) -> dict[str, Any]:
        return kwargs

    class BaseSettings(BaseModel):
        model_config = {"extra": "ignore"}

        @staticmethod
        def _load_env_file(env_file: str) -> dict[str, str]:
            path = Path(env_file)
            if not path.exists() or not path.is_file():
                return {}
            loaded: dict[str, str] = {}
            for raw_line in path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                loaded[key.strip()] = value.strip().strip("\"'")
            return loaded

        def __init__(self, **data: Any) -> None:
            config = getattr(self, "model_config", {}) or {}
            env_file = str(config.get("env_file", ".env"))
            case_sensitive = bool(config.get("case_sensitive", False))
            field_map = {
                (name if case_sensitive else name.lower()): name
                for name in self.__class__.model_fields.keys()
            }

            merged: dict[str, Any] = {}
            file_values = self._load_env_file(env_file)
            for key, value in file_values.items():
                normalized = key if case_sensitive else key.lower()
                field_name = field_map.get(normalized)
                if field_name and field_name not in data:
                    merged[field_name] = value

            for key, value in os.environ.items():
                normalized = key if case_sensitive else key.lower()
                field_name = field_map.get(normalized)
                if field_name and field_name not in data:
                    merged[field_name] = value

            merged.update(data)
            super().__init__(**merged)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "EchoLabs by Eburon AI API"
    app_version: str = "1.0.0"
    environment: str = "dev"
    log_level: str = "INFO"

    ui_origin: str = "http://localhost:4173"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:4173"])

    data_root: Path = Path("/tmp/echolabs_data")

    echolabs_sugar: str = ""
    echolabs_salt: str = "https://api.elevenlabs.io"
    echolabs_lime: str = "echo-tts@v2.5"
    echolabs_pepper: bool = True
    echolabs_mint: str = "echo-stt@v2"
    echolabs_cocoa: str = "clone_mode_default"
    echolabs_vanilla: str = "realtime_mode_default"
    echolabs_ice: str = "120rpm"

    provider_tts_model_id: str = "eleven_turbo_v2_5"
    provider_stt_model_id: str = "scribe_v1"
    provider_realtime_mode_id: str = "default"
    default_voice_provider_id: str = "EXAVITQu4vr4xnSDxMaL"

    echolabs_demo_mode: bool = True
    provider_timeout_seconds: float = 45.0

    admin_token: str = "change-me-admin-token"

    tts_editor_enabled: bool = True
    ollama_base_url: str = "http://168.231.78.113:11434"
    ollama_model: str = "gpt-oss-20b"
    ollama_timeout_seconds: float = 6.0
    ollama_editor_ssml: bool = True
    ollama_short_text_words: int = 8
    ollama_min_similarity_ratio: float = 0.8

    max_upload_mb: int = 25
    max_audio_seconds: int = 300
    max_ws_audio_bytes: int = 8_000_000
    ws_audio_queue_limit: int = 200

    rate_limit_per_minute: int = 120
    session_memory_turns: int = 10

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return ["http://localhost:4173"]

    @property
    def uploads_dir(self) -> Path:
        return self.data_root / "uploads"

    @property
    def outputs_dir(self) -> Path:
        return self.data_root / "outputs"

    @property
    def voices_dir(self) -> Path:
        return self.data_root / "voices"

    @property
    def config_dir(self) -> Path:
        return self.data_root / "config"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
