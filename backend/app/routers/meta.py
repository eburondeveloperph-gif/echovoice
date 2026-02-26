from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import MetaFeatures, MetaResponse
from app.services.alias_models import public_alias_models

router = APIRouter(prefix="/v1", tags=["meta"])


@router.get("/meta", response_model=MetaResponse)
def meta() -> MetaResponse:
    return MetaResponse(
        brand="EchoLabs by Eburon AI",
        models=public_alias_models(),
        features=MetaFeatures(
            voice_cloning=True,
            streaming=True,
            realtime=True,
        ),
    )
