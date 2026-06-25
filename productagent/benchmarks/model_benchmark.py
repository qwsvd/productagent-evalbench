import json
import time
from pathlib import Path
from typing import Any

from productagent.benchmarks.benchmark_config import BenchmarkConfig
from productagent.benchmarks.cost_tracker import BudgetTracker, SOURCE_NOTE, estimate_cost, estimate_tokens
from productagent.benchmarks.performance_tracker import build_performance_report, summarize_performance
from productagent.data_loader import PROJECT_ROOT, load_task_set
from productagent.models.provider_response import normalize_provider_response
from productagent.run_metadata import create_run_metadata


def run_model_benchmark(
    config: BenchmarkConfig,
    project_root: str | Path | None = None,
) -> list[dict[str, Any]]:
    config.validate()
    root = Path(project_root) if project_root else PROJECT_ROOT
    tasks = load_task_set(config.task_set, project_root=root)[: config.max_tasks]
    records: list[dict[str, Any]] = []
    budget = BudgetTracker(config.budget_usd)

    for provider_name in config.providers:
        for agent_name in config.agents:
            for task in tasks:
                record = _run_one(config, root, provider_name, agent_name, task, budget)
                records.append(record)
                if record.get("error_code") == "budget_exceeded":
                    break

    mock_records = [record for record in records if record.get("provider") == "mock"]
    external_records = [record for record in records if record.get("provider") != "mock"]
    if mock_records:
        _write_jsonl(mock_records, root / "outputs" / "model_benchmark_mock.jsonl")
    if external_records:
        _write_jsonl(external_records, root / "outputs" / "model_benchmark_external.jsonl")
    if not external_records and not (root / "outputs" / "model_benchmark_external.jsonl").exists():
        _write_jsonl([], root / "outputs" / "model_benchmark_external.jsonl")

    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "model_benchmark_report.md").write_text(_build_benchmark_report(records, config), encoding="utf-8")
    (reports_dir / "model_performance_comparison.md").write_text(build_performance_report(records), encoding="utf-8")
    (reports_dir / "model_cost_report.md").write_text(_build_cost_report(records), encoding="utf-8")
    return records


def _run_one(
    config: BenchmarkConfig,
    root: Path,
    provider_name: str,
    agent_name: str,
    task: dict[str, Any],
    budget: BudgetTracker,
) -> dict[str, Any]:
    from productagent.cli import build_agent, build_provider, provider_config_statuses

    provider_status = provider_config_statuses().get(provider_name, "missing_api_key")
    eval_mode = "mock" if provider_name == "mock" else "external"
    metadata = create_run_metadata(agent_name, provider_name, config.task_set, eval_mode, provider_status)
    provider_mode = metadata["provider_mode"]
    input_tokens = estimate_tokens(task.get("user_query", ""))

    base = {
        "run_id": metadata["run_id"],
        "provider": provider_name,
        "model": _model_name(provider_name),
        "agent": agent_name,
        "task_id": task["task_id"],
        "provider_mode": provider_mode,
        "eval_mode": eval_mode,
        "dry_run": config.dry_run,
        "input_tokens_estimated": input_tokens,
        "output_tokens_estimated": 0,
        "estimated_cost_usd": 0.0 if provider_name == "mock" else None,
        "latency_ms": None,
        "answer": "",
        "error_code": None,
        "error_message": None,
        "token_usage": {},
    }

    if provider_name != "mock" and not config.real_run:
        return {
            **base,
            "status": "error",
            "error_code": "dry_run_external_skipped",
            "error_message": "External provider was not called because --real-run was not set.",
        }
    if provider_name != "mock" and provider_status != "configured":
        return {
            **base,
            "status": "error",
            "error_code": "provider_not_configured",
            "error_message": f"{provider_name} is missing API key or provider configuration.",
        }
    if provider_name != "mock":
        projected_cost = estimate_cost(provider_name, input_tokens, config.max_output_tokens or 0)["estimated_cost_usd"]
        if not budget.can_spend(projected_cost):
            return {**base, **budget.budget_exceeded_result()}

    if provider_name != "mock" and not budget.can_spend():
        return {**base, **budget.budget_exceeded_result()}

    provider = build_provider(provider_name)
    if provider_name != "mock":
        setattr(provider, "timeout_seconds", config.timeout_seconds)
        setattr(provider, "max_output_tokens", config.max_output_tokens)
    agent = build_agent(agent_name, provider, project_root=root, top_k=3)
    started = time.perf_counter()
    result = agent.run_task(task)
    latency_ms = int((time.perf_counter() - started) * 1000)
    provider_text, provider_response = normalize_provider_response(
        provider_name,
        result.get("provider_response", result.get("final_answer", "")),
    )
    answer = result.get("final_answer") or provider_text
    output_tokens = estimate_tokens(answer)
    cost = estimate_cost(provider_name, input_tokens, output_tokens)
    budget.add_cost(cost["estimated_cost_usd"])
    return {
        **base,
        "status": provider_response.get("status", "ok"),
        "answer": answer,
        "latency_ms": provider_response.get("latency_ms") or latency_ms,
        "output_tokens_estimated": output_tokens,
        "estimated_cost_usd": cost["estimated_cost_usd"],
        "error_code": provider_response.get("error_code"),
        "error_message": provider_response.get("error_message"),
        "token_usage": provider_response.get("token_usage", {}),
        "price_source_note": SOURCE_NOTE,
    }


def _model_name(provider_name: str) -> str:
    defaults = {
        "mock": "mock",
        "deepseek": "deepseek-chat",
        "qwen": "qwen-plus",
        "openai": "gpt-4o-mini",
        "gemini": "gemini-1.5-flash",
        "claude": "claude-haiku",
    }
    return defaults.get(provider_name, "unknown")


def _write_jsonl(records: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def _build_benchmark_report(records: list[dict[str, Any]], config: BenchmarkConfig) -> str:
    providers = sorted({record["provider"] for record in records})
    missing = sorted({record["provider"] for record in records if record.get("error_code") == "provider_not_configured"})
    lines = [
        "# Model Benchmark Report",
        "",
        f"- Providers: {', '.join(providers) if providers else 'none'}",
        f"- Dry run: {config.dry_run}",
        f"- Real run: {config.real_run}",
        f"- Max tasks: {config.max_tasks}",
        f"- Budget USD: {config.budget_usd}",
        f"- Missing-key providers: {', '.join(missing) if missing else 'none'}",
        "",
        "This report does not fabricate DeepSeek/Qwen/OpenAI/Gemini/Claude performance. External providers are only called when `--real-run` is explicitly set and provider configuration is available.",
        "",
    ]
    return "\n".join(lines)


def _build_cost_report(records: list[dict[str, Any]]) -> str:
    summaries = summarize_performance(records)
    lines = [
        "# Model Cost Report",
        "",
        f"- Price source note: {SOURCE_NOTE}",
        "",
        "| Provider | Agent | Estimated Cost USD | Tasks | Notes |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for summary in summaries:
        lines.append(
            f"| {summary['provider']} | {summary['agent']} | {summary['estimated_cost_usd']:.6f} | {summary['tasks_run']} | {summary['notes']} |"
        )
    return "\n".join(lines) + "\n"
