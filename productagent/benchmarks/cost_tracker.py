from dataclasses import dataclass
from typing import Any


PRICE_TABLE = {
    "mock": {"input_per_1k": 0.0, "output_per_1k": 0.0, "tier": "free"},
    "deepseek": {"input_per_1k": 0.0002, "output_per_1k": 0.0004, "tier": "cheap"},
    "qwen": {"input_per_1k": 0.0003, "output_per_1k": 0.0006, "tier": "cheap"},
    "openai": {"input_per_1k": 0.001, "output_per_1k": 0.003, "tier": "medium"},
    "gemini": {"input_per_1k": 0.0008, "output_per_1k": 0.002, "tier": "medium"},
    "claude": {"input_per_1k": 0.003, "output_per_1k": 0.015, "tier": "medium/high"},
}

SOURCE_NOTE = "Estimated only. Check official pricing before real runs."


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def estimate_cost(provider: str, input_tokens: int, output_tokens: int) -> dict[str, Any]:
    price = PRICE_TABLE.get(provider)
    if price is None:
        return {"estimated_cost_usd": None, "price_tier": "unknown", "source_note": SOURCE_NOTE}
    cost = (input_tokens / 1000 * price["input_per_1k"]) + (output_tokens / 1000 * price["output_per_1k"])
    return {
        "estimated_cost_usd": round(cost, 6),
        "price_tier": price["tier"],
        "source_note": SOURCE_NOTE,
    }


@dataclass
class BudgetTracker:
    budget_usd: float | None
    spent_usd: float = 0.0

    def can_spend(self, next_cost: float | None = None) -> bool:
        if self.budget_usd is None:
            return True
        if self.budget_usd <= 0:
            return False
        return self.spent_usd + (next_cost or 0.0) <= self.budget_usd

    def add_cost(self, cost_usd: float | None) -> None:
        if cost_usd is not None:
            self.spent_usd += cost_usd

    def budget_exceeded_result(self) -> dict[str, Any]:
        return {
            "status": "error",
            "error_code": "budget_exceeded",
            "error_message": "Estimated benchmark budget was exceeded.",
            "estimated_cost_usd": self.spent_usd,
        }
