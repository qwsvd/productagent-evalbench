from pathlib import Path
from typing import Any

from productagent.data_loader import PROJECT_ROOT
from productagent.models.base import BaseProvider
from productagent.rag.retriever import SimpleKeywordRetriever
from productagent.tracing import TraceLogger


class RagAgent:
    """A minimal RAG agent that retrieves product-doc context before answering."""

    name = "rag"

    def __init__(
        self,
        provider: BaseProvider,
        retriever: SimpleKeywordRetriever | None = None,
        docs_dir: str | Path | None = None,
        top_k: int = 3,
        trace_logger: TraceLogger | None = None,
    ) -> None:
        self.provider = provider
        self.top_k = top_k
        self.trace_logger = trace_logger or TraceLogger()
        self.retriever = retriever or SimpleKeywordRetriever(
            docs_dir=Path(docs_dir) if docs_dir else PROJECT_ROOT / "data" / "product_docs"
        )

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
            retrieved_context = self.retriever.retrieve(user_query, top_k=self.top_k)
            self._log(
                trace_id=trace_id,
                task_id=task_id,
                event_type="retrieval",
                payload={"query": user_query, "result_count": len(retrieved_context)},
            )

            final_answer = self.provider.generate(
                user_query=user_query,
                task_type=task_type,
                expected_answer_points=expected_answer_points,
                required_tools=required_tools,
                risk_points=risk_points,
                retrieved_context=retrieved_context,
            )
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
            "retrieved_context": retrieved_context,
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

    def _log(self, *, trace_id: str, task_id: str, event_type: str, payload: dict[str, Any]) -> None:
        self.trace_logger.log(
            trace_id=trace_id,
            task_id=task_id,
            agent=self.name,
            provider=self.provider.name,
            event_type=event_type,
            payload=payload,
        )
