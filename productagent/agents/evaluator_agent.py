from typing import Any

from productagent.eval.metrics import context_usage_score, hallucination_risk, task_success_score, tool_call_accuracy


class EvaluatorAgent:
    """Offline critic that evaluates one result with deterministic rules."""

    name = "evaluator"

    def evaluate(self, task: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
        risk_result = result.get("risk_check") or {"risk_level": "low", "risk_points": []}
        success_score = task_success_score(result.get("final_answer", ""), task.get("expected_answer_points", []))
        tool_score = tool_call_accuracy(result, task)
        context_score = context_usage_score(result)
        risk_score = hallucination_risk(risk_result)

        risk_flags = list(risk_result.get("risk_points", []))
        missing_context = context_score == 0 and result.get("agent") in {"rag", "tool"}
        suggested_fix = "No obvious fix needed."
        if success_score < 1:
            suggested_fix = "Cover missing expected answer points."
        elif tool_score is not None and tool_score < 1:
            suggested_fix = "Review route_reason and required tool mapping."
        elif missing_context:
            suggested_fix = "Add or improve retrieved context."
        elif risk_score > 0:
            suggested_fix = "Rewrite answer to remove risky promises."

        return {
            "groundedness": "grounded" if context_score > 0 or result.get("agent") == "baseline" else "weak_context",
            "tool_use_quality": "not_applicable" if tool_score is None else ("good" if tool_score >= 0.95 else "needs_review"),
            "risk_flags": risk_flags,
            "missing_context": missing_context,
            "suggested_fix": suggested_fix,
            "scores": {
                "task_success_score": success_score,
                "tool_call_accuracy": tool_score,
                "context_usage_score": context_score,
                "hallucination_risk": risk_score,
            },
        }
