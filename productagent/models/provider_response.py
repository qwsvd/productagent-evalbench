from typing import Any


def normalize_provider_response(provider_name: str, response: str | dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Return text plus structured metadata for string and dict provider outputs."""

    if isinstance(response, dict):
        text = str(response.get("text") or response.get("error_message") or "")
        if not text:
            text = f"Provider `{provider_name}` returned no text."
        return text, response

    text = str(response)
    return text, {
        "provider": provider_name,
        "status": "ok",
        "text": text,
    }
