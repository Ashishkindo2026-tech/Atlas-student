from atlas_core.config import AtlasConfig


def test_config_defaults_are_local_first():
    config = AtlasConfig()
    assert config.ollama_base_url == "http://127.0.0.1:11434"
    assert config.ollama_model
    assert config.history_limit == 50


def test_config_environment_overrides(monkeypatch):
    monkeypatch.setenv("ATLAS_OLLAMA_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("ATLAS_OLLAMA_MODEL", "test-model")
    monkeypatch.setenv("ATLAS_HISTORY_LIMIT", "20")
    monkeypatch.setenv("ATLAS_REQUEST_TIMEOUT", "30")

    config = AtlasConfig.from_environment()
    assert config.ollama_model == "test-model"
    assert config.history_limit == 20
    assert config.request_timeout_seconds == 30.0
