from productagent.models.openai_compatible_provider import OpenAICompatibleProvider


class GeminiProvider(OpenAICompatibleProvider):
    provider_name = "gemini"
    api_key_env = "GEMINI_API_KEY"
    base_url_env = "GEMINI_BASE_URL"
    model_env = "GEMINI_MODEL"
    timeout_env = "GEMINI_TIMEOUT_SECONDS"
    default_base_url = ""
    default_model = "gemini-1.5-flash"
