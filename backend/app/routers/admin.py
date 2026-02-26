from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import get_settings
from app.core.security import require_admin_token
from app.models.schemas import AdminConfigResponse, AdminConfigUpdate
from app.services.deps import get_storage
from app.services.guardrails import sanitize_payload
from app.services.storage import StorageService

router = APIRouter(prefix="/v1/admin", tags=["admin"], dependencies=[Depends(require_admin_token)])


@router.get("/config", response_model=AdminConfigResponse)
def get_admin_config(storage: StorageService = Depends(get_storage)) -> AdminConfigResponse:
    settings = get_settings()
    persisted = storage.load_admin_config()
    response = AdminConfigResponse(
        Sugar=persisted.get("Sugar", "***" if settings.echolabs_sugar else ""),
        Salt=persisted.get("Salt", settings.echolabs_salt),
        Lime=persisted.get("Lime", settings.echolabs_lime),
        Pepper=persisted.get("Pepper", settings.echolabs_pepper),
        Mint=persisted.get("Mint", settings.echolabs_mint),
        Cocoa=persisted.get("Cocoa", settings.echolabs_cocoa),
        Vanilla=persisted.get("Vanilla", settings.echolabs_vanilla),
        Ice=persisted.get("Ice", settings.echolabs_ice),
    )
    return AdminConfigResponse(**sanitize_payload(response.model_dump()))


@router.post("/config", response_model=AdminConfigResponse)
def update_admin_config(
    payload: AdminConfigUpdate,
    storage: StorageService = Depends(get_storage),
) -> AdminConfigResponse:
    updates = {key: value for key, value in payload.model_dump().items() if value is not None}
    storage.save_admin_config(updates)
    merged = storage.load_admin_config()
    response = AdminConfigResponse(
        Sugar=merged.get("Sugar", ""),
        Salt=merged.get("Salt", ""),
        Lime=merged.get("Lime", "echo-tts@v2.5"),
        Pepper=bool(merged.get("Pepper", True)),
        Mint=merged.get("Mint", "echo-stt@v2"),
        Cocoa=merged.get("Cocoa", "clone_mode_default"),
        Vanilla=merged.get("Vanilla", "realtime_mode_default"),
        Ice=merged.get("Ice", "120rpm"),
    )
    return AdminConfigResponse(**sanitize_payload(response.model_dump()))
