import re
from typing import Any

from productagent.tool_coverage import called_tool_names, split_required_tools, tool_matches


def task_success_score(final_answer: str, expected_answer_points: list[str] | None) -> float:
    expected_answer_points = expected_answer_points or []
    if not expected_answer_points:
        return 1.0

    covered = 0
    normalized_answer = final_answer.lower()
    answer_terms = _terms(final_answer)

    for expected_point in expected_answer_points:
        normalized_point = expected_point.lower()
        point_terms = _terms(expected_point)
        if normalized_point and normalized_point in normalized_answer:
            covered += 1
            continue
        if point_terms and len(point_terms & answer_terms) >= max(1, min(2, len(point_terms))):
            covered += 1

    return round(covered / len(expected_answer_points), 3)


def tool_call_accuracy(result: dict[str, Any], task: dict[str, Any]) -> float | None:
    required_tools = task.get("required_tools", []) or []
    if not required_tools:
        return None

    split_tools = split_required_tools(required_tools, task.get("tool_availability"))
    available_required_tools = split_tools["available"]
    if not available_required_tools:
        return None

    called_tools = called_tool_names(result)
    covered = 0
    for required_tool in available_required_tools:
        if tool_matches(called_tools, required_tool):
            covered += 1

    return round(covered / len(available_required_tools), 3)


def tool_call_accuracy_details(result: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    required_tools = task.get("required_tools", []) or []
    split_tools = split_required_tools(required_tools, task.get("tool_availability"))
    called_tools = called_tool_names(result)
    hit_tools = [
        tool_name
        for tool_name in split_tools["available"]
        if tool_matches(called_tools, tool_name)
    ]

    return {
        "required_tools_total": len(required_tools),
        "available_required_tools": split_tools["available"],
        "future_mock_unavailable_tools": split_tools["future_mock_unavailable"],
        "not_applicable_tools": split_tools["not_applicable"],
        "available_tool_hits": hit_tools,
        "available_tool_hit_count": len(hit_tools),
        "available_tool_total": len(split_tools["available"]),
        "future_mock_unavailable_count": len(split_tools["future_mock_unavailable"]),
        "not_applicable_count": len(split_tools["not_applicable"]),
    }


def hallucination_risk(risk_check_result: dict[str, Any] | None) -> float:
    risk_level = (risk_check_result or {}).get("risk_level", "low")
    if risk_level == "high":
        return 1.0
    if risk_level == "medium":
        return 0.5
    return 0.0


def context_usage_score(result: dict[str, Any]) -> float:
    if result.get("retrieved_context"):
        return 1.0

    for call in result.get("tool_calls", []):
        if not isinstance(call, dict):
            continue
        tool_name = call.get("tool_name")
        tool_result = call.get("result")
        if tool_name == "search_docs" and tool_result:
            return 1.0
        if str(tool_name).startswith("read_") and isinstance(tool_result, dict) and tool_result.get("found"):
            return 1.0
    return 0.0


def user_experience_score(final_answer: str, risk_check_result: dict[str, Any] | None = None) -> float:
    normalized = final_answer.lower()
    score = 0.35

    if len(final_answer.strip()) >= 80:
        score += 0.2
    if any(token in normalized for token in ["because", "based on", "explain", "基于", "因为", "说明"]):
        score += 0.15
    if any(token in normalized for token in ["next", "suggest", "recommend", "please", "建议", "引导", "需要"]):
        score += 0.2
    risk = hallucination_risk(risk_check_result)
    if risk == 0:
        score += 0.2
    elif risk == 1:
        score -= 0.35
    else:
        score -= 0.15

    return round(max(0.0, min(1.0, score)), 3)


def evaluate_result(result: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    risk_result = result.get("risk_check") or {"risk_level": "low", "risk_points": []}
    final_answer = result.get("final_answer", "")
    accuracy_details = tool_call_accuracy_details(result, task)
    return {
        "task_success_score": task_success_score(final_answer, task.get("expected_answer_points", [])),
        "tool_call_accuracy": tool_call_accuracy(result, task),
        "hallucination_risk": hallucination_risk(risk_result),
        "context_usage_score": context_usage_score(result),
        "user_experience_score": user_experience_score(final_answer, risk_result),
        **accuracy_details,
    }


def _terms(text: str) -> set[str]:
    normalized = text.lower()
    terms = set(re.findall(r"[a-z0-9_]{3,}", normalized))
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", text)
    for index in range(len(cjk_chars) - 1):
        terms.add("".join(cjk_chars[index : index + 2]))
    return terms

