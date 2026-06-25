import json
from pathlib import Path
from typing import Any

from productagent.agents import EvaluatorAgent
from productagent.data_loader import PROJECT_ROOT, load_task_set
from productagent.eval import evaluate_agent_results
from productagent.eval.context_experiment import build_context_engineering_report, build_experiment_matrix
from productagent.eval.optimization_report import build_ablation_report, build_optimization_report


def run_experiments(project_root: str | Path | None = None) -> list[dict[str, Any]]:
    """Run local mock context-engineering experiments and write reports."""

    from productagent.cli import run_task_set

    root = Path(project_root) if project_root else PROJECT_ROOT
    reports_dir = root / "reports"
    outputs_dir = root / "outputs"
    reports_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    tasks = load_task_set("product_tasks", project_root=root)
    matrix = build_experiment_matrix()
    summaries: list[dict[str, Any]] = []
    evaluator = EvaluatorAgent()
    evaluator_feedback: list[dict[str, Any]] = []

    for experiment in matrix:
        output_path = outputs_dir / f"experiment_{experiment['name']}.jsonl"
        results = run_task_set(
            agent_name=experiment["agent"],
            provider_name="mock",
            task_set="product_tasks",
            output_path=output_path,
            project_root=root,
            top_k=experiment["top_k"],
            memory_mode=experiment["memory_mode"],
        )
        evaluated = evaluate_agent_results(experiment["agent"], results, tasks)
        summaries.append(_summarize_experiment(experiment, evaluated, output_path, root))

        if experiment["agent"] == "tool" and not evaluator_feedback:
            for item in evaluated[:5]:
                evaluator_feedback.append(
                    {
                        "task_id": item["task_id"],
                        "experiment": experiment["name"],
                        "evaluator_feedback": evaluator.evaluate(item["task"], item["result"]),
                    }
                )

    matrix_payload = {
        "project": "ProductAgent-EvalBench",
        "phase": "Phase 6",
        "provider": "mock",
        "notes": [
            "Experiments are local mock runs only.",
            "They do not claim real DeepSeek/Qwen/OpenAI/Gemini/Claude model performance.",
        ],
        "experiments": summaries,
    }
    (reports_dir / "experiment_matrix.json").write_text(
        json.dumps(matrix_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (reports_dir / "optimization_report.md").write_text(
        build_optimization_report(summaries),
        encoding="utf-8",
    )
    (reports_dir / "ablation_report.md").write_text(
        build_ablation_report(summaries),
        encoding="utf-8",
    )
    (reports_dir / "context_engineering_report.md").write_text(
        build_context_engineering_report(),
        encoding="utf-8",
    )
    (reports_dir / "evaluator_agent_report.md").write_text(
        _build_evaluator_report(evaluator_feedback),
        encoding="utf-8",
    )

    print(f"Saved experiment matrix to {reports_dir / 'experiment_matrix.json'}")
    print(f"Saved optimization report to {reports_dir / 'optimization_report.md'}")
    print(f"Saved ablation report to {reports_dir / 'ablation_report.md'}")
    print(f"Saved context engineering report to {reports_dir / 'context_engineering_report.md'}")
    print(f"Saved evaluator agent report to {reports_dir / 'evaluator_agent_report.md'}")
    return summaries


def _summarize_experiment(
    experiment: dict[str, Any],
    evaluated: list[dict[str, Any]],
    output_path: Path,
    root: Path,
) -> dict[str, Any]:
    return {
        "name": experiment["name"],
        "agent": experiment["agent"],
        "top_k": experiment["top_k"],
        "memory_mode": experiment["memory_mode"],
        "skills": experiment["skills"],
        "mcp_catalog": experiment["mcp_catalog"],
        "output": _display_path(output_path, root),
        "task_count": len(evaluated),
        "avg_task_success_score": _average(evaluated, "task_success_score"),
        "avg_tool_call_accuracy": _average_optional(evaluated, "tool_call_accuracy"),
        "avg_hallucination_risk": _average(evaluated, "hallucination_risk"),
        "avg_context_usage_score": _average(evaluated, "context_usage_score"),
        "avg_user_experience_score": _average(evaluated, "user_experience_score"),
    }


def _build_evaluator_report(feedback_items: list[dict[str, Any]]) -> str:
    lines = [
        "# Evaluator Agent Report",
        "",
        "The evaluator agent is a minimal offline critic. It uses heuristic eval metrics and does not call a real model.",
        "",
        "| Task | Experiment | Groundedness | Tool Use | Suggested Fix |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in feedback_items:
        feedback = item["evaluator_feedback"]
        lines.append(
            "| {task_id} | {experiment} | {groundedness} | {tool_use_quality} | {suggested_fix} |".format(
                task_id=item["task_id"],
                experiment=item["experiment"],
                groundedness=feedback["groundedness"],
                tool_use_quality=feedback["tool_use_quality"],
                suggested_fix=feedback["suggested_fix"].replace("|", "/"),
            )
        )
    if not feedback_items:
        lines.append("| none | none | none | none | No evaluator feedback generated. |")
    lines.extend(
        [
            "",
            "Evaluator feedback is used for offline diagnosis, not as a production-grade multi-agent system.",
            "",
        ]
    )
    return "\n".join(lines)


def _average(evaluated: list[dict[str, Any]], metric_name: str) -> float:
    if not evaluated:
        return 0.0
    return round(sum(item["metrics"][metric_name] for item in evaluated) / len(evaluated), 3)


def _average_optional(evaluated: list[dict[str, Any]], metric_name: str) -> float:
    values = [
        item["metrics"][metric_name]
        for item in evaluated
        if item["metrics"].get(metric_name) is not None
    ]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
