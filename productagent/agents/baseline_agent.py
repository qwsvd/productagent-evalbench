from typing import Any

from productagent.models.base import BaseProvider


class BaselineAgent:
    """A minimal agent that passes each task directly to one provider."""

    name = "baseline"

    def __init__(self, provider: BaseProvider) -> None:
        self.provider = provider

    def run(
        self,
        task_id: str,
        user_query: str,
        task_type: str,
        expected_answer_points: list[str] | None = None,
        required_tools: list[str] | None = None,
        risk_points: list[str] | None = None,
    ) -> dict[str, Any]:
        expected_answer_points = expected_answer_points or []
        required_tools = required_tools or []
        risk_points = risk_points or []

        final_answer = self.provider.generate(
            user_query=user_query,
            task_type=task_type,
            expected_answer_points=expected_answer_points,
            required_tools=required_tools,
            risk_points=risk_points,
        )

        return {
            "task_id": task_id,
            "agent": self.name,
            "provider": self.provider.name,
            "user_query": user_query,
            "final_answer": final_answer,
            "expected_answer_points": expected_answer_points,
            "risk_points": risk_points,
        }

    def run_task(self, task: dict[str, Any]) -> dict[str, Any]:
        return self.run(
            task_id=task["task_id"],
            user_query=task["user_query"],
            task_type=task["task_type"],
            expected_answer_points=task.get("expected_answer_points", []),
            required_tools=task.get("required_tools", []),
            risk_points=task.get("risk_points", []),
        )