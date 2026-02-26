from app.services.audio_utils import normalize_pcm16le, resample_pcm16le, synth_demo_wav, wav_duration_ms


def test_synth_demo_wav_has_duration() -> None:
    wav = synth_demo_wav("hello world")
    assert wav.startswith(b"RIFF")
    assert wav_duration_ms(wav) > 0


def test_normalize_pcm16le_returns_bytes() -> None:
    raw = b"\x01\x00\x02\x00\x03\x00\x04\x00"
    normalized = normalize_pcm16le(raw)
    assert isinstance(normalized, bytes)
    assert len(normalized) == len(raw)


def test_resample_pcm16le_changes_size() -> None:
    raw = (b"\x00\x00\x10\x00") * 128
    resampled = resample_pcm16le(raw, src_rate=16000, dst_rate=8000)
    assert len(resampled) < len(raw)
