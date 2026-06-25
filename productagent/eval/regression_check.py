import json
import subprocess
from pathlib import Path
from typing import Any

from productagent.data_loader import PROJECT_ROOT, load_task_set
from productagent.eval.metrics import tool_call_accuracy_details


def run_regression_check(project_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(project_root) if project_root else PROJECT_ROOT
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    checks = [
        _file_exists(root, "reports/benchmark_manifest.json"),
        _file_exists(root, "reports/provider_eval_isolation.md"),
        _file_exists(root, "reports/model_benchmark_report.md"),
        _file_exists(root, "outputs/agent_trace.jsonl"),
        _mock_eval_isolated(root),
        _tool_accuracy_at_least(root, threshold=0.95),
        _model_benchmark_dry_run_marked(root),
        _env_not_tracked(root),
    ]
    summary = {
        "project": "ProductAgent-EvalBench",
        "phase": "Phase 6",
        "status": "ok" if all(item["passed"] for item in checks) else "failed",
        "checks": checks,
    }
    report_path = reports_dir / "regression_check.md"
    report_path.write_text(_build_report(summary), encoding="utf-8")
    print(f"Saved regression check to {report_path}")
    return summary


def _file_exists(root: Path, relative_path: str) -> dict[str, Any]:
    return {
        "name": f"file_exists:{relative_path}",
        "passed": (root / relative_path).exists(),
        "details": relative_path,
    }


def _mock_eval_isolated(root: Path) -> dict[str, Any]:
    paths = [
        root / "outputs" / "baseline_mock_results.jsonl",
        root / "outputs" / "rag_mock_results.jsonl",
        root / "outputs" / "tool_mock_results.jsonl",
    ]
    external_records: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        for record in _read_jsonl(path):
            if record.get("provider") != "mock" or record.get("provider_mode") != "mock":
                external_records.append(f"{path.name}:{record.get('task_id')}")
    return {
        "name": "mock_eval_isolation",
        "passed": not external_records,
        "details": external_records or "mock outputs contain provider=mock and provider_mode=mock",
    }


def _tool_accuracy_at_least(root: Path, threshold: float) -> dict[str, Any]:
    result_path = root / "outputs" / "tool_mock_results.jsonl"
    if not result_path.exists():
        return {"name": "tool_strict_accuracy", "passed": False, "details": "missing tool_mock_results.jsonl"}

    tasks = {task["task_id"]: task for task in load_task_set("product_tasks", project_root=root)}
    hit_count = 0
    total = 0
    for record in _read_jsonl(result_path):
        task = tasks.get(record.get("task_id"), {})
        details = tool_call_accuracy_details(record, task)
        hit_count += details["available_tool_hit_count"]
        total += details["available_tool_total"]
    accuracy = hit_count / total if total else 0.0
    return {
        "name": "tool_strict_accuracy",
        "passed": accuracy >= threshold,
        "details": {"hit_count": hit_count, "total": total, "accuracy": round(accuracy, 3)},
    }


def _model_benchmark_dry_run_marked(root: Path) -> dict[str, Any]:
    path = root / "outputs" / "model_benchmark_mock.jsonl"
    if not path.exists():
        return {"name": "model_benchmark_dry_run_marked", "passed": False, "details": "missing model_benchmark_mock.jsonl"}
    records = _read_jsonl(path)
    missing = [record.get("task_id") for record in records if record.get("dry_run") is not True]
    return {
        "name": "model_benchmark_dry_run_marked",
        "passed": not missing,
        "details": missing or "all model benchmark mock records have dry_run=true",
    }


def _env_not_tracked(root: Path) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["git", "ls-files", ".env"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        tracked = [line for line in completed.stdout.splitlines() if line.strip()]
    except OSError:
        tracked = []
    return {
        "name": "env_not_tracked",
        "passed": not tracked,
        "details": tracked or ".env is not tracked by git",
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _build_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Regression Check",
        "",
        f"- Phase: {summary['phase']}",
        f"- Status: {summary['status']}",
        "",
        "| Check | Passed | Details |",
        "| --- | --- | --- |",
    ]
    for check in summary["checks"]:
        lines.append(
            f"| {check['name']} | {check['passed']} | {json.dumps(check['details'], ensure_ascii=False)} |"
        )
    lines.extend(
        [
            "",
            "This check is local-only. It does not run pytest itself and does not call external model providers.",
            "",
        ]
    )
    return "\n".join(lines)
