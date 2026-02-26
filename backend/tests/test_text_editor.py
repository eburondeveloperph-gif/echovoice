from app.core.config import Settings
from app.services.text_editor import TTSTextEditor


def test_short_text_gets_light_edit() -> None:
    settings = Settings(tts_editor_enabled=True, ollama_short_text_words=8)
    editor = TTSTextEditor(settings)

    edited = editor._light_edit("hello how are you")
    assert edited == "Hello, how are you?"


def test_ssml_wrap_for_edited_output() -> None:
    settings = Settings(tts_editor_enabled=True, ollama_editor_ssml=True)
    editor = TTSTextEditor(settings)

    out = editor._finalize_output("hello how are you", "Hello, how are you?")
    assert out.startswith("<speak>")
    assert "Hello, how are you?" in out


def test_similarity_guard_prevents_rewrite() -> None:
    settings = Settings(tts_editor_enabled=True, ollama_editor_ssml=False)
    editor = TTSTextEditor(settings)

    out = editor._finalize_output("hello how are you", "The weather is sunny and warm")
    assert out == "Hello, how are you?"
