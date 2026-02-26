import base64
import io
import wave

from fastapi.testclient import TestClient

from app.main import app


def _wav_bytes() -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 1600)
    return buf.getvalue()


def test_tts_returns_audio_url() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/v1/tts",
            json={
                "text": "hello",
                "voice_id": "echo_voice_demo",
                "format": "wav",
                "latency_mode": "balanced",
                "nuance": 0.9,
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["audio_url"].startswith("/files/")


def test_stt_returns_transcript() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/v1/stt",
            files={"audio": ("sample.wav", _wav_bytes(), "audio/wav")},
            data={"language": "en", "diarization": "false"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert "transcript" in payload


def test_voice_clone_and_list() -> None:
    with TestClient(app) as client:
        clone = client.post(
            "/v1/voice/clone",
            data={"name": "Demo Voice"},
            files=[("samples", ("sample.wav", _wav_bytes(), "audio/wav"))],
        )
        assert clone.status_code == 200
        voice_id = clone.json()["voice_id"]

        listed = client.get("/v1/voice/list")
        assert listed.status_code == 200
        voices = listed.json()["voices"]
        assert any(item["voice_id"] == voice_id for item in voices)

        preview = client.post(f"/v1/voice/preview/{voice_id}")
        assert preview.status_code == 200
        preview_payload = preview.json()
        assert preview_payload["preview_text"] == "HI THIS IS ECHO VOICE FROM EBURON AI"
        assert preview_payload["audio_url"].startswith("/files/")


def test_convo_turn_endpoint() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/v1/convo/turn",
            json={
                "session_id": "turn_test_1",
                "text": "Hello agent",
                "latency_mode": "balanced",
                "nuance": 0.9,
                "agent_prompt": "Be concise",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["audio_url"].startswith("/files/")
        assert "agent_text" in payload


def test_realtime_ws_flow() -> None:
    with TestClient(app) as client:
        with client.websocket_connect("/v1/convo/ws?session_id=test_session") as websocket:
            state = websocket.receive_json()
            assert state["type"] == "state"

            websocket.send_json({"type": "start", "session_id": "test_session", "voice_id": "echo_voice_demo"})
            websocket.receive_json()

            chunk_b64 = base64.b64encode(_wav_bytes()).decode("ascii")
            websocket.send_json({"type": "audio", "chunk_b64": chunk_b64, "codec": "audio/wav", "seq": 1})
            websocket.send_json({"type": "stop"})

            seen_types: set[str] = set()
            for _ in range(30):
                message = websocket.receive_json()
                msg_type = str(message.get("type"))
                seen_types.add(msg_type)
                if (
                    "stt_final" in seen_types
                    and "agent_final" in seen_types
                    and "tts_audio" in seen_types
                    and msg_type == "state"
                    and message.get("state") == "listening"
                ):
                    break

            assert "stt_final" in seen_types
            assert "agent_final" in seen_types
            assert "tts_audio" in seen_types
