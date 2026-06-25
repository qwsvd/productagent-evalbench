import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


COMMANDS = [
    [sys.executable, "-m", "productagent.cli", "providers"],
    [sys.executable, "-m", "productagent.cli", "skills"],
    [sys.executable, "-m", "productagent.cli", "mcp-tools"],
    [sys.executable, "-m", "productagent.cli", "run", "--agent", "tool", "--provider", "mock", "--task-set", "product_tasks"],
    [
        sys.executable,
        "-m",
        "productagent.cli",
        "run",
        "--agent",
        "tool",
        "--provider",
        "mock",
        "--task-set",
        "product_tasks",
        "--memory-mode",
        "session",
    ],
    [
        sys.executable,
        "-m",
        "productagent.cli",
        "compare",
        "--agents",
        "baseline,rag,tool",
        "--provider",
        "mock",
        "--task-set",
        "product_tasks",
    ],
    [sys.executable, "-m", "productagent.cli", "experiments"],
    [
        sys.executable,
        "-m",
        "productagent.cli",
        "model-benchmark",
        "--providers",
        "mock",
        "--agents",
        "tool",
        "--task-set",
        "product_tasks",
        "--max-tasks",
        "3",
        "--dry-run",
    ],
    [sys.executable, "-m", "productagent.cli", "regression-check"],
]


EXPECTED_FILES = [
    "outputs/tool_mock_results.jsonl",
    "outputs/agent_trace.jsonl",
    "outputs/model_benchmark_mock.jsonl",
    "reports/eval_summary.md",
    "reports/failure_analysis.md",
    "reports/tool_trace_report.md",
    "reports/provider_eval_isolation.md",
    "reports/benchmark_manifest.json",
    "reports/model_benchmark_report.md",
    "reports/model_performance_comparison.md",
    "reports/model_cost_report.md",
    "reports/experiment_matrix.json",
    "reports/optimization_report.md",
    "reports/ablation_report.md",
    "reports/context_engineering_report.md",
    "reports/evaluator_agent_report.md",
    "reports/regression_check.md",
]


def main() -> int:
    for command in COMMANDS:
        print("+ " + " ".join(command))
        completed = subprocess.run(command, cwd=ROOT, text=True)
        if completed.returncode != 0:
            return completed.returncode

    missing = [path for path in EXPECTED_FILES if not (ROOT / path).exists()]
    if missing:
        print("Missing expected files:", ", ".join(missing))
        return 1

    print("Smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
