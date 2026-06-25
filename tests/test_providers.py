import json
from pathlib import Path

from productagent.cli import provider_config_statuses, run_task_set
from productagent.data_loader import PROJECT_ROOT
from productagent.models import (
    DeepSeekProvider,
    GeminiProvider,
    OpenAICompatibleProvider,
    OpenAIProvider,
    QwenProvider,
)


ALL_PROVIDER_ENV_VARS = [
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
    "QWEN_API_KEY",
    "QWEN_BASE_URL",
    "QWEN_MODEL",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL",
    "GEMINI_API_KEY",
    "GEMINI_BASE_URL",
    "GEMINI_MODEL",
]


class DummyProvider(OpenAICompatibleProvider):
    provider_name = "dummy"
    api_key_env = "DUMMY_API_KEY"
    base_url_env = "DUMMY_BASE_URL"
    model_env = "DUMMY_MODEL"
    timeout_env = "DUMMY_TIMEOUT_SECONDS"
    default_base_url = "https://example.invalid/v1"
    default_model = "dummy-model"


def _clear_provider_env(monkeypatch) -> None:
    for env_name in ALL_PROVIDER_ENV_VARS + [
        "DUMMY_API_KEY",
        "DUMMY_BASE_URL",
        "DUMMY_MODEL",
        "DUMMY_TIMEOUT_SECONDS",
    ]:
        monkeypatch.delenv(env_name, raising=False)


def test_openai_compatible_provider_missing_api_key_does_not_crash(monkeypatch) -> None:
    _clear_provider_env(monkeypatch)
    provider = DummyProvider()

    result = provider.generate(user_query="hello", task_type="product_qa")

    assert result["status"] == "error"
    assert result["error_code"] == "provider_not_configured"
    assert result["error_message"] == "Missing DUMMY_API_KEY"


def test_deepseek_provider_metadata(monkeypatch) -> None:
    _clear_provider_env(monkeypatch)
    provider = DeepSeekProvider()

    assert provider.name == "deepseek"
    assert provider.api_key_env == "DEEPSEEK_API_KEY"
    assert provider.base_url_env == "DEEPSEEK_BASE_URL"
    assert provider.model_env == "DEEPSEEK_MODEL"
    assert provider.model_name == "deepseek-chat"


def test_qwen_provider_metadata(monkeypatch) -> None:
    _clear_provider_env(monkeypatch)
    provider = QwenProvider()

    assert provider.name == "qwen"
    assert provider.api_key_env == "QWEN_API_KEY"
    assert provider.base_url_env == "QWEN_BASE_URL"
    assert provider.model_env == "QWEN_MODEL"
    assert provider.model_name == "qwen-plus"


def test_openai_provider_metadata(monkeypatch) -> None:
    _clear_provider_env(monkeypatch)
    provider = OpenAIProvider()

    assert provider.name == "openai"
    assert provider.api_key_env == "OPENAI_API_KEY"
    assert provider.base_url_env == "OPENAI_BASE_URL"
    assert provider.model_env == "OPENAI_MODEL"
    assert provider.model_name == "gpt-4o-mini"


def test_gemini_provider_metadata(monkeypatch) -> None:
    _clear_provider_env(monkeypatch)
    provider = GeminiProvider()

    assert provider.name == "gemini"
    assert provider.api_key_env == "GEMINI_API_KEY"
    assert provider.base_url_env == "GEMINI_BASE_URL"
    assert provider.model_env == "GEMINI_MODEL"
    assert provider.model_name == "gemini-1.5-flash"


def test_redact_config_does_not_expose_api_key(monkeypatch) -> None:
    _clear_provider_env(monkeypatch)
    sentinel_value = "redaction-" + "sentinel-value"
    monkeypatch.setenv("OPENAI_API_KEY", sentinel_value)
    provider = OpenAIProvider()

    redacted = provider.redact_config()

    assert redacted["api_key"] == "configured"
    assert sentinel_value not in json.dumps(redacted)


def test_provider_statuses_do_not_call_network(monkeypatch) -> None:
    _clear_provider_env(monkeypatch)

    assert provider_config_statuses() == {
        "mock": "available",
        "deepseek": "missing_api_key",
        "qwen": "missing_api_key",
        "openai": "missing_api_key",
        "gemini": "missing_api_key",
    }


def test_cli_recognizes_external_providers_without_keys(monkeypatch, tmp_path: Path) -> None:
    _clear_provider_env(monkeypatch)

    for provider_name in ["deepseek", "qwen", "openai", "gemini"]:
        output_path = tmp_path / f"baseline_{provider_name}_results.jsonl"
        results = run_task_set(
            agent_name="baseline",
            provider_name=provider_name,
            task_set="product_tasks",
            output_path=output_path,
            top_k=1,
        )

        assert output_path.exists()
        assert len(results) >= 20
        assert results[0]["provider"] == provider_name
        assert results[0]["provider_response"]["status"] == "error"
        assert results[0]["provider_response"]["error_code"] == "provider_not_configured"


def test_env_example_and_provider_docs_exist() -> None:
    assert (PROJECT_ROOT / ".env.example").exists()
    assert (PROJECT_ROOT / "docs" / "provider_setup.md").exists()


def test_gitignore_contains_env_patterns() -> None:
    content = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert ".env" in content
    assert "*.env" in content
    assert ".env.local" in content
    assert ".env.*.local" in content


def test_readme_contains_api_key_safety() -> None:
    content = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "Phase 4: OpenAI-compatible Model Providers" in content
    assert "Do not commit real API keys" in content
    assert "Mock provider runs the full local project without keys" in content
