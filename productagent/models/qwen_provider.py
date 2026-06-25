from productagent.models.openai_compatible_provider import OpenAICompatibleProvider


class QwenProvider(OpenAICompatibleProvider):
    provider_name = "qwen"
    api_key_env = "QWEN_API_KEY"
    base_url_env = "QWEN_BASE_URL"
    model_env = "QWEN_MODEL"
    timeout_env = "QWEN_TIMEOUT_SECONDS"
    default_base_url = ""
    default_model = "qwen-plus"
