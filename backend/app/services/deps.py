from __future__ import annotations

from starlette.requests import HTTPConnection

from app.services.provider_client import ProviderClient
from app.services.sessions import SessionManager
from app.services.storage import StorageService
from app.services.text_editor import TTSTextEditor


def get_storage(connection: HTTPConnection) -> StorageService:
    return connection.app.state.storage


def get_provider_client(connection: HTTPConnection) -> ProviderClient:
    return connection.app.state.provider_client


def get_sessions(connection: HTTPConnection) -> SessionManager:
    return connection.app.state.sessions


def get_text_editor(connection: HTTPConnection) -> TTSTextEditor:
    return connection.app.state.text_editor
