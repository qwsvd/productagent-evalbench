from typing import Any


REQUIRED_RESULT_FIELDS = [
    "task_id",
    "agent",
    "provider",
    "provider_mode",
    "run_id",
    "status",
    "schema_version",
]

REQUIRED_TRACE_FIELDS = [
    "trace_id",
    "task_id",
    "agent",
    "provider",
    "event_type",
    "payload",
    "timestamp",
]

REQUIRED_MANIFEST_FIELDS = [
    "project",
    "phase",
    "task_set",
    "agents",
    "provider",
    "provider_mode",
    "outputs",
    "reports",
    "schema_version",
]


def attach_result_metadata(record: dict[str, Any], run_metadata: dict[str, Any]) -> dict[str, Any]:
    """Return a stable result record with run and provider bookkeeping fields."""

    enriched = dict(record)
    provider_response = enriched.get("provider_response") or {}
    final_answer = enriched.get("final_answer", "")

    enriched["run_id"] = run_metadata["run_id"]
    enriched["timestamp"] = run_metadata["timestamp"]
    enriched["provider_mode"] = run_metadata["provider_mode"]
    enriched["eval_mode"] = run_metadata["eval_mode"]
    enriched["task_set"] = run_metadata["task_set"]
    enriched["project_phase"] = run_metadata["project_phase"]
    enriched["schema_version"] = run_metadata["schema_version"]
    enriched["status"] = provider_response.get("status", "ok")
    enriched["answer"] = final_answer
    enriched["text"] = final_answer
    enriched["error_code"] = provider_response.get("error_code")
    enriched["error_message"] = provider_response.get("error_message")
    enriched["latency_ms"] = provider_response.get("latency_ms")
    enriched["estimated_cost_usd"] = provider_response.get("estimated_cost_usd")
    enriched["token_usage"] = provider_response.get("token_usage") or {}
    enriched.setdefault("tool_calls", [])
    enriched.setdefault("route_reason", {})

    validation = validate_result_record(enriched)
    enriched["schema_validation"] = validation
    return enriched


def validate_result_record(record: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for field in REQUIRED_RESULT_FIELDS:
        if field not in record:
            errors.append(f"missing_field:{field}")

    if "answer" not in record and "text" not in record and "final_answer" not in record:
        errors.append("missing_field:answer_or_text")
    if "tool_calls" in record and not isinstance(record["tool_calls"], list):
        errors.append("invalid_type:tool_calls")
    if "route_reason" in record and not isinstance(record["route_reason"], dict):
        errors.append("invalid_type:route_reason")
    if "token_usage" in record and not isinstance(record["token_usage"], dict):
        errors.append("invalid_type:token_usage")

    return {"valid": not errors, "errors": errors}


def validate_trace_record(record: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for field in REQUIRED_TRACE_FIELDS:
        if field not in record:
            errors.append(f"missing_field:{field}")
    if "payload" in record and not isinstance(record["payload"], dict):
        errors.append("invalid_type:payload")
    return {"valid": not errors, "errors": errors}


def validate_report_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in manifest:
            errors.append(f"missing_field:{field}")
    if "outputs" in manifest and not isinstance(manifest["outputs"], list):
        errors.append("invalid_type:outputs")
    if "reports" in manifest and not isinstance(manifest["reports"], list):
        errors.append("invalid_type:reports")
    if "agents" in manifest and not isinstance(manifest["agents"], list):
        errors.append("invalid_type:agents")
    return {"valid": not errors, "errors": errors}
