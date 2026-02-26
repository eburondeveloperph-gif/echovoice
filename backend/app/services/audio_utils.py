from __future__ import annotations

import base64
import io
import math
import wave
from array import array
from typing import Iterable

import numpy as np


def normalize_pcm16le(raw: bytes) -> bytes:
    if not raw:
        return raw
    samples = array("h")
    samples.frombytes(raw)
    peak = max(abs(sample) for sample in samples) or 1
    gain = 32767 / peak
    normalized = array("h", [int(max(min(sample * gain, 32767), -32768)) for sample in samples])
    return normalized.tobytes()


def resample_pcm16le(raw: bytes, src_rate: int, dst_rate: int) -> bytes:
    if src_rate == dst_rate or not raw:
        return raw
    samples = np.frombuffer(raw, dtype=np.int16)
    if len(samples) == 0:
        return raw
    ratio = dst_rate / src_rate
    target_length = max(1, int(len(samples) * ratio))
    src_positions = np.linspace(0, len(samples) - 1, num=len(samples))
    dst_positions = np.linspace(0, len(samples) - 1, num=target_length)
    resampled = np.interp(dst_positions, src_positions, samples).astype(np.int16)
    return resampled.tobytes()


def chunk_bytes(payload: bytes, chunk_size: int) -> Iterable[bytes]:
    for i in range(0, len(payload), chunk_size):
        yield payload[i : i + chunk_size]


def wav_duration_ms(wav_bytes: bytes) -> int:
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        frame_rate = wav_file.getframerate()
        frames = wav_file.getnframes()
    if frame_rate <= 0:
        return 0
    return int((frames / frame_rate) * 1000)


def estimate_duration_ms(audio_bytes: bytes, fmt: str) -> int:
    if fmt == "wav":
        try:
            return wav_duration_ms(audio_bytes)
        except Exception:
            return 0
    # fallback estimate for compressed output
    return int((len(audio_bytes) / 16_000) * 1000)


def synth_demo_wav(text: str, sample_rate: int = 16000) -> bytes:
    duration_s = max(1.0, min(8.0, len(text) / 18.0))
    frequency = 360.0
    volume = 0.35
    frames = bytearray()

    for n in range(int(duration_s * sample_rate)):
        sample = volume * math.sin(2 * math.pi * frequency * (n / sample_rate))
        value = int(max(min(sample, 1.0), -1.0) * 32767)
        frames += value.to_bytes(2, byteorder="little", signed=True)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(bytes(frames))
    return buffer.getvalue()


def base64_chunks(payload: bytes, chunk_size: int = 12000) -> list[str]:
    return [base64.b64encode(chunk).decode("ascii") for chunk in chunk_bytes(payload, chunk_size)]


def decode_chunk_base64(chunk_b64: str) -> bytes:
    return base64.b64decode(chunk_b64.encode("ascii"), validate=False)
