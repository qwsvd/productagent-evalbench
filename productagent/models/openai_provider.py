from productagent.models.openai_compatible_provider import OpenAICompatibleProvider


class OpenAIProvider(OpenAICompatibleProvider):
    provider_name = "openai"
    api_key_env = "OPENAI_API_KEY"
    base_url_env = "OPENAI_BASE_URL"
    model_env = "OPENAI_MODEL"
    timeout_env = "OPENAI_TIMEOUT_SECONDS"
    default_base_url = "https://api.openai.com/v1"
    default_model = "gpt-4o-mini"
