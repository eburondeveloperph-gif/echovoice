from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import Settings


class StorageService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.uploads_dir = settings.uploads_dir
        self.outputs_dir = settings.outputs_dir
        self.voices_dir = settings.voices_dir
        self.config_dir = settings.config_dir
        self.voices_db = self.voices_dir / "voices.json"
        self.admin_config_file = self.config_dir / "config.json"

    def ensure_directories(self) -> None:
        for directory in [
            self.settings.data_root,
            self.uploads_dir,
            self.outputs_dir,
            self.voices_dir,
            self.config_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, upload_file: UploadFile, subdir: str = "") -> str:
        destination_dir = self.uploads_dir / subdir
        destination_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(upload_file.filename or "input.bin").suffix or ".bin"
        filename = f"{uuid4().hex}{suffix}"
        destination = destination_dir / filename
        content = await upload_file.read()
        destination.write_bytes(content)
        relative = destination.relative_to(self.settings.data_root)
        return relative.as_posix()

    def save_bytes(self, payload: bytes, suffix: str, subdir: str = "") -> str:
        destination_dir = self.outputs_dir / subdir
        destination_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid4().hex}{suffix}"
        destination = destination_dir / filename
        destination.write_bytes(payload)
        relative = destination.relative_to(self.settings.data_root)
        return relative.as_posix()

    def resolve_relative_path(self, relative_path: str) -> Path:
        candidate = (self.settings.data_root / relative_path).resolve()
        data_root = self.settings.data_root.resolve()
        if data_root not in candidate.parents and candidate != data_root:
            raise ValueError("Invalid path")
        if not candidate.exists() or not candidate.is_file():
            raise FileNotFoundError("File not found")
        return candidate

    def file_url(self, relative_path: str) -> str:
        return f"/files/{relative_path}"

    def _load_json_file(self, path: Path, default_value: Any) -> Any:
        if not path.exists():
            return default_value
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default_value

    def _save_json_file(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def list_voices(self, include_deleted: bool = False) -> list[dict[str, Any]]:
        data = self._load_json_file(self.voices_db, [])
        voices = [item for item in data if include_deleted or item.get("status") != "deleted"]
        return voices

    def get_voice(self, voice_id: str) -> dict[str, Any] | None:
        voices = self._load_json_file(self.voices_db, [])
        for voice in voices:
            if voice.get("voice_id") == voice_id:
                return voice
        return None

    def get_voice_by_provider_id(self, provider_voice_id: str) -> dict[str, Any] | None:
        voices = self._load_json_file(self.voices_db, [])
        for voice in voices:
            if voice.get("provider_voice_id") == provider_voice_id:
                return voice
        return None

    def upsert_voice(self, voice: dict[str, Any]) -> None:
        voices = self._load_json_file(self.voices_db, [])
        updated = False
        for index, item in enumerate(voices):
            if item.get("voice_id") == voice.get("voice_id"):
                voices[index] = voice
                updated = True
                break
        if not updated:
            voices.append(voice)
        self._save_json_file(self.voices_db, voices)

    def soft_delete_voice(self, voice_id: str) -> bool:
        voices = self._load_json_file(self.voices_db, [])
        found = False
        now = datetime.now(tz=timezone.utc).isoformat()
        for voice in voices:
            if voice.get("voice_id") == voice_id and voice.get("status") != "deleted":
                voice["status"] = "deleted"
                voice["updated_at"] = now
                found = True
                break
        if found:
            self._save_json_file(self.voices_db, voices)
        return found

    def load_admin_config(self) -> dict[str, Any]:
        return self._load_json_file(self.admin_config_file, {})

    def save_admin_config(self, payload: dict[str, Any]) -> None:
        existing = self.load_admin_config()
        existing.update(payload)
        self._save_json_file(self.admin_config_file, existing)
