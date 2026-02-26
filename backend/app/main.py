from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import get_settings
from app.core.cors import configure_cors
from app.core.logging import configure_logging, request_id_ctx
from app.routers import admin, convo, health, meta, stt, tts, voice
from app.services.guardrails import safe_error_message, sanitize_payload
from app.services.provider_client import ProviderClient
from app.services.rate_limit import InMemoryRateLimiter
from app.services.sessions import SessionManager
from app.services.storage import StorageService
from app.services.text_editor import TTSTextEditor

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("echolabs.api")

app = FastAPI(title=settings.app_name, version=settings.app_version)
configure_cors(app, settings)


@app.on_event("startup")
def on_startup() -> None:
    storage = StorageService(settings)
    storage.ensure_directories()

    app.state.storage = storage
    app.state.provider_client = ProviderClient(settings)
    app.state.text_editor = TTSTextEditor(settings)
    app.state.sessions = SessionManager(max_turns=settings.session_memory_turns)
    app.state.rate_limiter = InMemoryRateLimiter(max_requests=settings.rate_limit_per_minute)

    logger.info("startup-complete")


@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid4()))
    request_id_ctx.set(request_id)

    if request.url.path.startswith("/v1"):
        ip = request.client.host if request.client else "unknown"
        allowed = request.app.state.rate_limiter.allow(ip)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "code": "ECHO_RATE_LIMITED",
                    "message": "Too many requests. Please retry shortly.",
                    "request_id": request_id,
                },
            )

    response = await call_next(request)
    response.headers["x-request-id"] = request_id

    provider_headers = [header for header in response.headers if header.lower().startswith("x-eleven")]
    for header in provider_headers:
        del response.headers[header]

    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        content = sanitize_payload(detail)
        content.setdefault("message", safe_error_message(None))
    else:
        content = {"code": "ECHO_HTTP_ERROR", "message": safe_error_message(str(detail))}
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "code": "ECHO_VALIDATION_ERROR",
            "message": "Request validation failed.",
            "errors": sanitize_payload(exc.errors()),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled-exception")
    return JSONResponse(
        status_code=500,
        content={"code": "ECHO_INTERNAL_ERROR", "message": safe_error_message(str(exc))},
    )


@app.get("/files/{relative_path:path}")
def read_file(relative_path: str, request: Request) -> FileResponse:
    storage: StorageService = request.app.state.storage
    file_path = storage.resolve_relative_path(relative_path)
    return FileResponse(path=file_path)


@app.get("/metrics")
def metrics(request: Request) -> dict[str, str | int]:
    sessions: SessionManager = request.app.state.sessions
    return {
        "service": "echolabs_api",
        "ts": datetime.now(tz=timezone.utc).isoformat(),
        "sessions": len(sessions._sessions),
    }


app.include_router(health.router)
app.include_router(meta.router)
app.include_router(tts.router)
app.include_router(stt.router)
app.include_router(voice.router)
app.include_router(convo.router)
app.include_router(admin.router)
