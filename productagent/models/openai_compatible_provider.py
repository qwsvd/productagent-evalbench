import json
import os
import socket
import time
import urllib.error
import urllib.request
from typing import Any, Mapping, Sequence

from productagent.models.base import BaseProvider


class OpenAICompatibleProvider(BaseProvider):
    """Small stdlib-only provider for OpenAI-compatible chat completions APIs."""

    provider_name = "openai_compatible"
    api_key_env = ""
    base_url_env = ""
    model_env = ""
    timeout_env = ""
    default_base_url = ""
    default_model = ""
    default_timeout_seconds = 30

    @property
    def name(self) -> str:
        return self.provider_name

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model_name: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv(self.api_key_env, "")
        self.base_url = base_url if base_url is not None else os.getenv(self.base_url_env, self.default_base_url)
        self.model_name = model_name if model_name is not None else os.getenv(self.model_env, self.default_model)
        self.timeout_seconds = timeout_seconds if timeout_seconds is not None else self._env_timeout()

    def generate(
        self,
        user_query: str,
        task_type: str,
        expected_answer_points: Sequence[str] | None = None,
        required_tools: Sequence[str] | None = None,
        risk_points: Sequence[str] | None = None,
        retrieved_context: Sequence[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        start_time = time.perf_counter()
        config_error = self.validate_config()
        if config_error is not None:
            config_error["latency_ms"] = self._elapsed_ms(start_time)
            return config_error

        payload = self.build_payload(
            user_query=user_query,
            task_type=task_type,
            expected_answer_points=expected_answer_points,
            required_tools=required_tools,
            risk_points=risk_points,
            retrieved_context=retrieved_context,
        )
        try:
            request = self.build_request(payload)
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
            response_json = json.loads(response_body)
        except TimeoutError:
            return self.provider_error("provider_timeout", "Provider request timed out.", retryable=True, latency_ms=self._elapsed_ms(start_time))
        except socket.timeout:
            return self.provider_error("provider_timeout", "Provider request timed out.", retryable=True, latency_ms=self._elapsed_ms(start_time))
        except urllib.error.URLError as exc:
            if "timed out" in str(exc).lower():
                return self.provider_error("provider_timeout", "Provider request timed out.", retryable=True, latency_ms=self._elapsed_ms(start_time))
            return self.provider_error("provider_request_failed", "Provider request failed.", retryable=True, latency_ms=self._elapsed_ms(start_time))
        except OSError:
            return self.provider_error("provider_request_failed", "Provider request failed.", retryable=True, latency_ms=self._elapsed_ms(start_time))
        except json.JSONDecodeError:
            return self.provider_error("provider_response_invalid", "Provider returned invalid JSON.", retryable=False, latency_ms=self._elapsed_ms(start_time))

        parsed = self.parse_response(response_json)
        parsed["latency_ms"] = self._elapsed_ms(start_time)
        return parsed

    def build_payload(
        self,
        *,
        user_query: str,
        task_type: str,
        expected_answer_points: Sequence[str] | None = None,
        required_tools: Sequence[str] | None = None,
        risk_points: Sequence[str] | None = None,
        retrieved_context: Sequence[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        prompt = self._build_prompt(
            user_query=user_query,
            task_type=task_type,
            expected_answer_points=expected_answer_points,
            required_tools=required_tools,
            risk_points=risk_points,
            retrieved_context=retrieved_context,
        )
        return {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a product support agent. Answer from provided task context and avoid unsafe promises.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

    def build_request(self, payload: dict[str, Any]) -> urllib.request.Request:
        url = self._chat_completions_url()
        body = json.dumps(payload).encode("utf-8")
        return urllib.request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

    def parse_response(self, response_json: dict[str, Any]) -> dict[str, Any]:
        try:
            text = response_json["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return self.provider_error("provider_response_invalid", "Provider response did not include choices[0].message.content.")

        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "status": "ok",
            "text": str(text),
            "raw_response": response_json,
            "latency_ms": None,
            "estimated_cost_usd": None,
            "token_usage": response_json.get("usage", {}),
        }

    def validate_config(self) -> dict[str, Any] | None:
        if not self.api_key:
            return self.provider_error("provider_not_configured", f"Missing {self.api_key_env}", retryable=False)
        if not self.base_url:
            return self.provider_error("provider_not_configured", f"Missing {self.base_url_env}", retryable=False)
        if not self.model_name:
            return self.provider_error("provider_not_configured", f"Missing {self.model_env}", retryable=False)
        return None

    def redact_config(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "api_key_env": self.api_key_env,
            "api_key": "configured" if self.api_key else "missing",
            "base_url_env": self.base_url_env,
            "base_url": "configured" if self.base_url else "missing",
            "model_env": self.model_env,
            "model": self.model_name or "missing",
            "timeout_env": self.timeout_env,
            "timeout_seconds": self.timeout_seconds,
        }

    def provider_error(
        self,
        code: str,
        message: str,
        retryable: bool = False,
        latency_ms: int | None = None,
    ) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model_name or self.default_model,
            "status": "error",
            "error_code": code,
            "error_message": message,
            "retryable": retryable,
            "latency_ms": latency_ms,
            "estimated_cost_usd": None,
            "token_usage": {},
        }

    def _chat_completions_url(self) -> str:
        base_url = self.base_url.rstrip("/")
        if base_url.endswith("/chat/completions"):
            return base_url
        return f"{base_url}/chat/completions"

    def _env_timeout(self) -> int:
        raw_timeout = os.getenv(self.timeout_env, "")
        if not raw_timeout:
            return self.default_timeout_seconds
        try:
            parsed = int(raw_timeout)
        except ValueError:
            return self.default_timeout_seconds
        return max(1, parsed)

    def _elapsed_ms(self, start_time: float) -> int:
        return int((time.perf_counter() - start_time) * 1000)

    def _build_prompt(
        self,
        *,
        user_query: str,
        task_type: str,
        expected_answer_points: Sequence[str] | None = None,
        required_tools: Sequence[str] | None = None,
        risk_points: Sequence[str] | None = None,
        retrieved_context: Sequence[Mapping[str, Any]] | None = None,
    ) -> str:
        lines = [
            f"Task type: {task_type}",
            f"User query: {user_query}",
        ]
        if expected_answer_points:
            lines.append("Expected answer points:")
            lines.extend(f"- {point}" for point in expected_answer_points)
        if required_tools:
            lines.append("Required tools:")
            lines.extend(f"- {tool}" for tool in required_tools)
        if risk_points:
            lines.append("Risk points:")
            lines.extend(f"- {risk}" for risk in risk_points)
        if retrieved_context:
            lines.append("Retrieved context:")
            for item in retrieved_context:
                source = item.get("source_file", "unknown")
                content = item.get("content", "")
                lines.append(f"- Source: {source}\n  Content: {content}")
        lines.append("Answer concisely and state when policy or user state needs verification.")
        return "\n".join(lines)
