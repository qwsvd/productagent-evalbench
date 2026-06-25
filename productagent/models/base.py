from abc import ABC, abstractmethod
from typing import Any, Mapping, Sequence


class BaseProvider(ABC):
    """Minimal provider interface for model-like answer generation."""

    name: str

    @abstractmethod
    def generate(
        self,
        user_query: str,
        task_type: str,
        expected_answer_points: Sequence[str] | None = None,
        required_tools: Sequence[str] | None = None,
        risk_points: Sequence[str] | None = None,
        retrieved_context: Sequence[Mapping[str, Any]] | None = None,
    ) -> str | dict[str, Any]:
        """Return a final answer for one product task."""
