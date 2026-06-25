from typing import Any, Callable

from productagent.mcp.tool_catalog import build_tool_catalog
from productagent.tools import (
    check_order_state,
    check_risk_state,
    check_usage_state,
    check_user_state,
    classify_issue,
    create_ticket,
    read_policy,
    risk_check,
    search_docs,
)


SAFE_TOOLS: dict[str, Callable[..., Any]] = {
    "search_docs": search_docs,
    "read_policy": read_policy,
    "check_user_state": check_user_state,
    "check_order_state": check_order_state,
    "check_usage_state": check_usage_state,
    "check_risk_state": check_risk_state,
    "classify_issue": classify_issue,
    "create_ticket": create_ticket,
    "risk_check": risk_check,
}


def handle_jsonrpc_request(request: dict[str, Any]) -> dict[str, Any]:
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}

    if method == "initialize":
        return _result(request_id, {"name": "productagent-local-mcp", "version": "0.1"})
    if method == "tools/list":
        return _result(request_id, {"tools": build_tool_catalog()})
    if method == "tools/call":
        return _handle_tool_call(request_id, params)
    return _error(request_id, "method_not_found", f"Unsupported method: {method}")


def _handle_tool_call(request_id: Any, params: dict[str, Any]) -> dict[str, Any]:
    tool_name = params.get("name")
    arguments = params.get("arguments") or {}
    if not isinstance(arguments, dict):
        return _error(request_id, "invalid_arguments", "arguments must be an object")
    tool = SAFE_TOOLS.get(str(tool_name))
    if tool is None:
        return _error(request_id, "tool_not_found", f"Unknown tool: {tool_name}")
    try:
        result = tool(**arguments)
    except TypeError as exc:
        return _error(request_id, "invalid_arguments", str(exc))
    except Exception as exc:
        return _error(request_id, "tool_call_failed", str(exc))
    return _result(request_id, {"content": result})


def _result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: str, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
