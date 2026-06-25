from dataclasses import dataclass


@dataclass
class BenchmarkConfig:
    providers: list[str]
    agents: list[str]
    task_set: str
    max_tasks: int = 5
    dry_run: bool = True
    real_run: bool = False
    budget_usd: float | None = None
    max_output_tokens: int | None = None
    timeout_seconds: int = 60

    def validate(self) -> None:
        if self.max_tasks <= 0:
            raise ValueError("max_tasks must be positive")
        if self.max_tasks > 20:
            raise ValueError("max_tasks is capped at 20 for safety")
        if self.real_run:
            if self.budget_usd is None or self.budget_usd <= 0:
                raise ValueError("--real-run requires --budget-usd > 0")
            if self.max_output_tokens is None or self.max_output_tokens <= 0:
                raise ValueError("--real-run requires --max-output-tokens")
        if self.dry_run and self.real_run:
            raise ValueError("Use either --dry-run or --real-run, not both")
