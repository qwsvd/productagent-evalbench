from typing import Any


AVAILABLE_TOOLS = {
    "search_docs",
    "read_policy",
    "check_user_state",
    "check_order_state",
    "check_usage_state",
    "check_risk_state",
    "classify_issue",
    "create_ticket",
    "risk_check",
}

FUTURE_MOCK_UNAVAILABLE_TOOLS = {
    "check_payment_state",
    "check_invoice_state",
}

TOOL_ALIASES = {
    "read_feature_guide": "read_policy",
    "read_refund_policy": "read_policy",
    "read_account_policy": "read_policy",
    "read_faq": "read_policy",
    "read_risk_rules": "read_policy",
    "check_account_state": "check_user_state",
}

VALID_AVAILABILITY_STATUSES = {
    "available",
    "future_mock_unavailable",
    "not_applicable",
}


def normalize_tool_name(tool_name: str) -> str:
    normalized = tool_name.strip().lower()
    return TOOL_ALIASES.get(normalized, normalized)


def normalize_required_tools(required_tools: list[str] | None) -> list[str]:
    normalized_tools: list[str] = []
    for tool_name in required_tools or []:
        normalized = normalize_tool_name(str(tool_name))
        if normalized not in normalized_tools:
            normalized_tools.append(normalized)
    return normalized_tools


def infer_tool_availability(required_tools: list[str] | None) -> dict[str, str]:
    availability: dict[str, str] = {}
    for tool_name in required_tools or []:
        normalized = normalize_tool_name(str(tool_name))
        if normalized in AVAILABLE_TOOLS:
            availability[normalized] = "available"
        elif normalized in FUTURE_MOCK_UNAVAILABLE_TOOLS:
            availability[normalized] = "future_mock_unavailable"
        else:
            availability[normalized] = "not_applicable"
    return availability


def normalize_tool_availability(
    required_tools: list[str] | None,
    tool_availability: dict[str, str] | None,
) -> dict[str, str]:
    inferred = infer_tool_availability(required_tools)
    for tool_name, status in (tool_availability or {}).items():
        normalized_tool = normalize_tool_name(str(tool_name))
        normalized_status = str(status).strip().lower()
        if normalized_status not in VALID_AVAILABILITY_STATUSES:
            normalized_status = "not_applicable"
        inferred[normalized_tool] = normalized_status
    return inferred


def split_required_tools(
    required_tools: list[str] | None,
    tool_availability: dict[str, str] | None = None,
) -> dict[str, list[str]]:
    normalized_required_tools = normalize_required_tools(required_tools)
    normalized_availability = normalize_tool_availability(normalized_required_tools, tool_availability)

    split = {
        "available": [],
        "future_mock_unavailable": [],
        "not_applicable": [],
    }
    for tool_name in normalized_required_tools:
        status = normalized_availability.get(tool_name, "not_applicable")
        split[status].append(tool_name)
    return split


def called_tool_names(result: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for call in result.get("tool_calls", []):
        if not isinstance(call, dict):
            continue
        tool_name = str(call.get("tool_name", "")).lower()
        if tool_name:
            names.add(tool_name)
            names.add(normalize_tool_name(tool_name))
    return names


def tool_matches(called_tools: set[str], required_tool: str) -> bool:
    normalized_required = normalize_tool_name(required_tool)
    return normalized_required in called_tools
