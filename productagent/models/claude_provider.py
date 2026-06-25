from productagent.models.openai_compatible_provider import OpenAICompatibleProvider


class ClaudeProvider(OpenAICompatibleProvider):
    provider_name = "claude"
    api_key_env = "ANTHROPIC_API_KEY"
    base_url_env = "CLAUDE_BASE_URL"
    model_env = "CLAUDE_MODEL"
    timeout_env = "CLAUDE_TIMEOUT_SECONDS"
    default_base_url = ""
    default_model = "claude-haiku"
