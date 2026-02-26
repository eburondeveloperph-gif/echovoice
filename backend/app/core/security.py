from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


BRAND_SAFE_AUTH_MESSAGE = "Access denied by EchoLabs access policy."


def require_admin_token(authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "ECHO_AUTH_REQUIRED", "message": BRAND_SAFE_AUTH_MESSAGE},
        )
    token = authorization.split(" ", 1)[1].strip()
    if not token or token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ECHO_AUTH_FORBIDDEN", "message": BRAND_SAFE_AUTH_MESSAGE},
        )
