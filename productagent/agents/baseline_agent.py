from typing import Any

from productagent.models.base import BaseProvider
from productagent.models.provider_response import normalize_provider_response
from productagent.tracing import TraceLogger


class BaselineAgent:
    """A minimal agent that passes each task directly to one provider."""

    name = "baseline"

    def __init__(self, provider: BaseProvider, trace_logger: TraceLogger | None = None) -> None:
        self.provider = provider
        self.trace_logger = trace_logger or TraceLogger()

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
        trace_id = self.trace_logger.new_trace_id()
        self._log(
            trace_id=trace_id,
            task_id=task_id,
            event_type="task_start",
            payload={"user_query": user_query, "task_type": task_type},
        )

        try:
            provider_output = self.provider.generate(
                user_query=user_query,
                task_type=task_type,
                expected_answer_points=expected_answer_points,
                required_tools=required_tools,
                risk_points=risk_points,
            )
            final_answer, provider_response = normalize_provider_response(self.provider.name, provider_output)
        except Exception as exc:
            self._log(
                trace_id=trace_id,
                task_id=task_id,
                event_type="error",
                payload={"error": str(exc)},
            )
            raise

        self._log(
            trace_id=trace_id,
            task_id=task_id,
            event_type="final_answer",
            payload={"final_answer": final_answer},
        )
        self._log(
            trace_id=trace_id,
            task_id=task_id,
            event_type="task_end",
            payload={"status": "ok"},
        )

        return {
            "task_id": task_id,
            "agent": self.name,
            "provider": self.provider.name,
            "user_query": user_query,
            "final_answer": final_answer,
            "provider_response": provider_response,
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

    def _log(self, *, trace_id: str, task_id: str, event_type: str, payload: dict[str, Any]) -> None:
        self.trace_logger.log(
            trace_id=trace_id,
            task_id=task_id,
            agent=self.name,
            provider=self.provider.name,
            event_type=event_type,
            payload=payload,
        )
