import uuid
from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = "1.0"
PROJECT_PHASE = "Phase 5"


def create_run_metadata(
    agent_name: str,
    provider_name: str,
    task_set: str,
    eval_mode: str = "mock",
    provider_config_status: str | None = None,
) -> dict[str, Any]:
    """Create run metadata without secrets or personal information."""

    timestamp = datetime.now(timezone.utc).isoformat()
    short_uuid = uuid.uuid4().hex[:8]
    normalized_provider = provider_name.strip().lower()
    normalized_eval_mode = _normalize_eval_mode(eval_mode, normalized_provider)

    return {
        "run_id": f"{timestamp.replace(':', '').replace('+', 'Z')}-{short_uuid}",
        "timestamp": timestamp,
        "agent": agent_name.strip().lower(),
        "provider": normalized_provider,
        "provider_mode": _provider_mode(normalized_provider, normalized_eval_mode, provider_config_status),
        "eval_mode": normalized_eval_mode,
        "task_set": task_set,
        "project_phase": PROJECT_PHASE,
        "schema_version": SCHEMA_VERSION,
    }


def _normalize_eval_mode(eval_mode: str, provider_name: str) -> str:
    if provider_name == "mock":
        return "mock"
    if eval_mode == "mock":
        return "external"
    return "external" if eval_mode == "external" else eval_mode


def _provider_mode(provider_name: str, eval_mode: str, provider_config_status: str | None) -> str:
    if provider_name == "mock" or eval_mode == "mock":
        return "mock"
    if provider_config_status == "configured":
        return "external_configured"
    return "external_missing_key"
