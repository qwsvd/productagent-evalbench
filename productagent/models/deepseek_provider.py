from productagent.models.openai_compatible_provider import OpenAICompatibleProvider


class DeepSeekProvider(OpenAICompatibleProvider):
    provider_name = "deepseek"
    api_key_env = "DEEPSEEK_API_KEY"
    base_url_env = "DEEPSEEK_BASE_URL"
    model_env = "DEEPSEEK_MODEL"
    timeout_env = "DEEPSEEK_TIMEOUT_SECONDS"
    default_base_url = ""
    default_model = "deepseek-chat"
