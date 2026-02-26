from app.core.config import Settings
from app.services.alias_models import enforce_nuance, public_alias_models, resolve_alias_config


def test_alias_models_are_public_and_stable() -> None:
    aliases = public_alias_models()
    assert aliases == ["echo-tts@v2.5", "echo-stt@v2", "echo-realtime@v1"]


def test_high_nuance_is_enforced() -> None:
    assert enforce_nuance(0.2) >= 0.7
    assert enforce_nuance(0.95) == 0.95


def test_alias_config_maps_to_provider_fields() -> None:
    settings = Settings(echolabs_sugar="", echolabs_demo_mode=True)
    config = resolve_alias_config(settings)
    assert config.tts_alias == "echo-tts@v2.5"
    assert config.stt_alias == "echo-stt@v2"
    assert config.realtime_alias == "echo-realtime@v1"
