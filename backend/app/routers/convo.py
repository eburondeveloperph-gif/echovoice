from __future__ import annotations

import asyncio
import json
from uuid import uuid4

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.models.schemas import ConvoTurnRequest, ConvoTurnResponse
from app.services.alias_models import resolve_alias_config
from app.services.audio_utils import base64_chunks, decode_chunk_base64
from app.services.deps import get_provider_client, get_sessions, get_storage
from app.services.guardrails import is_provider_identity_question, provider_identity_message, sanitize_payload
from app.services.provider_client import ProviderClient
from app.services.sessions import SessionManager
from app.services.storage import StorageService

router = APIRouter(prefix="/v1/convo", tags=["convo"])


def build_agent_reply(user_text: str, agent_prompt: str | None = None) -> str:
    if is_provider_identity_question(user_text):
        return provider_identity_message()
    if not user_text.strip():
        return "I did not catch that. Please try again."

    prompt_context = ""
    if agent_prompt and agent_prompt.strip():
        prompt_context = f"[{agent_prompt.strip()[:240]}] "

    return (
        f"{prompt_context}EchoLabs agent response: "
        + user_text.strip()[:300]
        + " | I can continue in natural voice with low-latency turn handling."
    )


async def stream_agent_text(websocket: WebSocket, text: str) -> None:
    words = text.split(" ")
    buffer: list[str] = []
    for index, word in enumerate(words):
        buffer.append(word)
        if (index + 1) % 4 == 0:
            await websocket.send_json({"type": "agent_delta", "text_delta": " ".join(buffer) + " "})
            buffer.clear()
            await asyncio.sleep(0.04)
    if buffer:
        await websocket.send_json({"type": "agent_delta", "text_delta": " ".join(buffer)})


@router.post("/turn", response_model=ConvoTurnResponse)
async def convo_turn(
    body: ConvoTurnRequest,
    provider: ProviderClient = Depends(get_provider_client),
    sessions: SessionManager = Depends(get_sessions),
    storage: StorageService = Depends(get_storage),
) -> ConvoTurnResponse:
    session_id = body.session_id or f"session_{uuid4().hex[:10]}"
    session = sessions.get_or_create(session_id)

    session.voice_id = body.voice_id or session.voice_id
    session.latency_mode = body.latency_mode
    session.nuance = body.nuance
    if body.agent_prompt is not None:
        session.agent_prompt = body.agent_prompt

    assistant_text = build_agent_reply(body.text, session.agent_prompt)
    sessions.append_turn(session_id=session_id, user=body.text, assistant=assistant_text)

    tts_audio, _, duration_ms = await provider.tts(
        text=assistant_text,
        voice_id=session.voice_id,
        fmt="wav",
        latency_mode=session.latency_mode,
        nuance=session.nuance,
    )
    relative_path = storage.save_bytes(tts_audio, suffix=".wav", subdir="convo")

    response = ConvoTurnResponse(
        session_id=session_id,
        user_text=body.text,
        agent_text=assistant_text,
        audio_url=storage.file_url(relative_path),
        duration_ms=duration_ms,
        meta={"model_alias": resolve_alias_config(provider.settings).realtime_alias},
    )
    return ConvoTurnResponse(**sanitize_payload(response.model_dump()))


@router.websocket("/ws")
async def convo_ws(
    websocket: WebSocket,
    provider: ProviderClient = Depends(get_provider_client),
    sessions: SessionManager = Depends(get_sessions),
) -> None:
    await websocket.accept()

    session_id = websocket.query_params.get("session_id") or f"session_{uuid4().hex[:10]}"
    state = sessions.get_or_create(session_id)
    audio_queue: list[bytes] = []
    received_bytes = 0

    await websocket.send_json({"type": "state", "state": "listening", "session_id": session_id})

    try:
        while True:
            raw = await websocket.receive_text()
            message = json.loads(raw)
            message_type = message.get("type")

            if message_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if message_type == "start":
                state.voice_id = message.get("voice_id") or state.voice_id
                prefs = message.get("prefs") or {}
                state.latency_mode = prefs.get("latency_mode", state.latency_mode)
                state.nuance = float(prefs.get("nuance", state.nuance))
                state.agent_prompt = prefs.get("agent_prompt", state.agent_prompt)
                await websocket.send_json({"type": "state", "state": "listening"})
                continue

            if message_type == "audio":
                chunk_b64 = message.get("chunk_b64", "")
                chunk = decode_chunk_base64(chunk_b64)

                if len(audio_queue) >= provider.settings.ws_audio_queue_limit:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "code": "ECHO_WS_QUEUE_FULL",
                            "message": "Realtime queue is full. Stop and restart capture.",
                        }
                    )
                    continue

                received_bytes += len(chunk)
                if received_bytes > provider.settings.max_ws_audio_bytes:
                    audio_queue.clear()
                    received_bytes = 0
                    await websocket.send_json(
                        {
                            "type": "error",
                            "code": "ECHO_WS_AUDIO_LIMIT",
                            "message": "Audio limit exceeded for this session.",
                        }
                    )
                    continue

                audio_queue.append(chunk)
                if len(audio_queue) % 3 == 0:
                    await websocket.send_json(
                        {
                            "type": "stt_partial",
                            "text": f"Listening... ({len(audio_queue)} chunks)",
                        }
                    )
                continue

            if message_type == "stop":
                await websocket.send_json({"type": "state", "state": "thinking"})

                audio_blob = b"".join(audio_queue)
                audio_queue.clear()
                received_bytes = 0

                if not audio_blob:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "code": "ECHO_WS_EMPTY_AUDIO",
                            "message": "No audio received.",
                        }
                    )
                    await websocket.send_json({"type": "state", "state": "listening"})
                    continue

                stt_result = await provider.stt_from_bytes(audio_blob, suffix=".webm")
                user_text = stt_result.get("transcript", "")
                await websocket.send_json({"type": "stt_final", "text": user_text})

                assistant_text = build_agent_reply(user_text, state.agent_prompt)
                await stream_agent_text(websocket, assistant_text)
                await websocket.send_json({"type": "agent_final", "text": assistant_text})

                sessions.append_turn(session_id=session_id, user=user_text, assistant=assistant_text)

                await websocket.send_json({"type": "state", "state": "speaking"})
                tts_audio, codec, _ = await provider.tts(
                    text=assistant_text,
                    voice_id=state.voice_id,
                    fmt="wav",
                    latency_mode=state.latency_mode,
                    nuance=state.nuance,
                )

                for seq, chunk_b64 in enumerate(base64_chunks(tts_audio, chunk_size=12000)):
                    await websocket.send_json(
                        {
                            "type": "tts_audio",
                            "chunk_b64": chunk_b64,
                            "codec": codec,
                            "seq": seq,
                        }
                    )

                await websocket.send_json({"type": "state", "state": "listening"})
                continue

            await websocket.send_json(
                {
                    "type": "error",
                    "code": "ECHO_WS_BAD_MESSAGE",
                    "message": "Unsupported websocket message type.",
                }
            )
    except WebSocketDisconnect:
        return
