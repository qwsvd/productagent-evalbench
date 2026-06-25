import argparse
from pathlib import Path
from typing import Any

from productagent.agents import BaselineAgent, RagAgent, ToolAgent
from productagent.data_loader import PROJECT_ROOT, load_task_set
from productagent.eval import evaluate_results_by_agent
from productagent.eval.report_writer import (
    build_eval_summary,
    build_failure_analysis,
    build_tool_trace_report,
)
from productagent.models import MockProvider
from productagent.output_writer import write_jsonl, write_markdown
from productagent.tracing import TraceLogger


SUPPORTED_AGENTS = {"baseline", "rag", "tool"}


def build_provider(provider_name: str) -> MockProvider:
    if provider_name == "mock":
        return MockProvider()
    raise ValueError(f"Unsupported provider: {provider_name}")


def build_agent(
    agent_name: str,
    provider: MockProvider,
    project_root: Path,
    top_k: int = 3,
    trace_logger: TraceLogger | None = None,
) -> BaselineAgent | RagAgent | ToolAgent:
    docs_dir = project_root / "data" / "product_docs"
    if agent_name == "baseline":
        return BaselineAgent(provider=provider, trace_logger=trace_logger)
    if agent_name == "rag":
        return RagAgent(provider=provider, docs_dir=docs_dir, top_k=top_k, trace_logger=trace_logger)
    if agent_name == "tool":
        return ToolAgent(provider=provider, docs_dir=docs_dir, top_k=top_k, trace_logger=trace_logger)
    raise ValueError(f"Unsupported agent: {agent_name}")


def run_task_set(
    agent_name: str,
    provider_name: str,
    task_set: str,
    output_path: str | Path | None = None,
    project_root: str | Path | None = None,
    top_k: int = 3,
    trace_logger: TraceLogger | None = None,
) -> list[dict[str, Any]]:
    root = Path(project_root) if project_root else PROJECT_ROOT
    normalized_agent = _normalize_agent_name(agent_name)
    if normalized_agent not in SUPPORTED_AGENTS:
        raise ValueError(f"Unsupported agent: {agent_name}")

    provider = build_provider(provider_name)
    trace_logger = trace_logger or TraceLogger(root / "outputs" / "agent_trace.jsonl")
    agent = build_agent(normalized_agent, provider, project_root=root, top_k=top_k, trace_logger=trace_logger)
    tasks = load_task_set(task_set, project_root=root)

    results = [agent.run_task(task) for task in tasks]
    final_output_path = output_path or root / "outputs" / f"{normalized_agent}_{provider_name}_results.jsonl"
    write_jsonl(results, final_output_path)

    print(f"Ran {len(results)} tasks with agent={normalized_agent}, provider={provider_name}")
    print(f"Saved results to {final_output_path}")
    for result in results:
        first_line = result["final_answer"].splitlines()[0]
        if normalized_agent == "rag":
            context_count = len(result.get("retrieved_context", []))
            print(f"- {result['task_id']}: {first_line} retrieved_context={context_count}")
        elif normalized_agent == "tool":
            tool_count = len(result.get("tool_calls", []))
            risk_level = result.get("risk_check", {}).get("risk_level", "unknown")
            print(f"- {result['task_id']}: {first_line} tool_calls={tool_count} risk={risk_level}")
        else:
            print(f"- {result['task_id']}: {first_line}")

    return results


def compare_agents(
    agent_names: list[str],
    provider_name: str,
    task_set: str,
    project_root: str | Path | None = None,
    top_k: int = 3,
) -> Path:
    root = Path(project_root) if project_root else PROJECT_ROOT
    normalized_agents = [_normalize_agent_name(agent_name) for agent_name in agent_names if agent_name.strip()]
    for agent_name in normalized_agents:
        if agent_name not in SUPPORTED_AGENTS:
            raise ValueError(f"Unsupported agent in compare: {agent_name}")

    tasks = load_task_set(task_set, project_root=root)
    trace_path = root / "outputs" / "agent_trace.jsonl"
    trace_logger = TraceLogger(trace_path)
    trace_logger.clear()

    results_by_agent: dict[str, list[dict[str, Any]]] = {}
    output_paths: dict[str, Path] = {}
    for agent_name in normalized_agents:
        output_path = root / "outputs" / f"{agent_name}_{provider_name}_results.jsonl"
        results_by_agent[agent_name] = run_task_set(
            agent_name=agent_name,
            provider_name=provider_name,
            task_set=task_set,
            output_path=output_path,
            project_root=root,
            top_k=top_k,
            trace_logger=trace_logger,
        )
        output_paths[agent_name] = output_path

    evaluated_by_agent = evaluate_results_by_agent(results_by_agent, tasks)
    reports_dir = root / "reports"

    eval_summary_path = reports_dir / "eval_summary.md"
    failure_analysis_path = reports_dir / "failure_analysis.md"
    tool_trace_report_path = reports_dir / "tool_trace_report.md"
    write_markdown(
        build_eval_summary(
            evaluated_by_agent=evaluated_by_agent,
            output_paths=output_paths,
            task_count=len(tasks),
            project_root=root,
        ),
        eval_summary_path,
    )
    write_markdown(build_failure_analysis(evaluated_by_agent), failure_analysis_path)
    write_markdown(
        build_tool_trace_report(
            trace_path=trace_path,
            project_root=root,
            evaluated_by_agent=evaluated_by_agent,
        ),
        tool_trace_report_path,
    )

    return_path = eval_summary_path
    if "baseline" in results_by_agent and "rag" in results_by_agent:
        rag_report = build_comparison_report(results_by_agent, output_paths, project_root=root)
        rag_report_path = reports_dir / "rag_comparison.md"
        write_markdown(rag_report, rag_report_path)
        if set(normalized_agents) == {"baseline", "rag"}:
            return_path = rag_report_path

    print(f"Saved eval summary to {eval_summary_path}")
    print(f"Saved failure analysis to {failure_analysis_path}")
    print(f"Saved tool trace report to {tool_trace_report_path}")
    return return_path


def build_comparison_report(
    results_by_agent: dict[str, list[dict[str, Any]]],
    output_paths: dict[str, Path],
    project_root: Path | None = None,
) -> str:
    baseline_results = results_by_agent.get("baseline", [])
    rag_results = results_by_agent.get("rag", [])
    task_count = max(len(baseline_results), len(rag_results))
    used_docs = sorted(
        {
            item["source_file"]
            for result in rag_results
            for item in result.get("retrieved_context", [])
            if item.get("source_file")
        }
    )

    baseline_path = _display_path(
        output_paths.get("baseline", Path("outputs/baseline_mock_results.jsonl")),
        project_root,
    )
    rag_path = _display_path(
        output_paths.get("rag", Path("outputs/rag_mock_results.jsonl")),
        project_root,
    )
    used_docs_text = "\n".join(f"- {doc}" for doc in used_docs) if used_docs else "- No retrieved docs."

    return "\n".join(
        [
            "# RAG Comparison Report",
            "",
            f"- Total tasks: {task_count}",
            f"- Baseline output: `{baseline_path}`",
            f"- RAG output: `{rag_path}`",
            "",
            "## Retrieved Docs",
            "",
            used_docs_text,
            "",
            "## RAG Improvements Over Baseline",
            "",
            "- RAG retrieves product documents before calling the provider.",
            "- RAG results include `retrieved_context` for inspection.",
            "- Product-policy answers are more grounded in local Markdown docs.",
            "",
            "## Current Limitations",
            "",
            "- Retrieval is keyword-based, not vector search.",
            "- `MockProvider` is deterministic and does not represent a real model.",
            "- This report is kept for backwards compatibility; see `reports/eval_summary.md` for the Phase 3 eval report.",
            "",
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ProductAgent-EvalBench tasks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a task set.")
    run_parser.add_argument("--agent", default="baseline", choices=sorted(SUPPORTED_AGENTS))
    run_parser.add_argument("--provider", default="mock", choices=["mock"])
    run_parser.add_argument("--task-set", default="product_tasks")
    run_parser.add_argument("--top-k", type=int, default=3)

    compare_parser = subparsers.add_parser("compare", help="Compare multiple agents.")
    compare_parser.add_argument("--agents", default="baseline,rag")
    compare_parser.add_argument("--provider", default="mock", choices=["mock"])
    compare_parser.add_argument("--task-set", default="product_tasks")
    compare_parser.add_argument("--top-k", type=int, default=3)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        run_task_set(
            agent_name=args.agent,
            provider_name=args.provider,
            task_set=args.task_set,
            top_k=args.top_k,
        )
        return 0

    if args.command == "compare":
        compare_agents(
            agent_names=args.agents.split(","),
            provider_name=args.provider,
            task_set=args.task_set,
            top_k=args.top_k,
        )
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


def _normalize_agent_name(agent_name: str) -> str:
    return agent_name.strip().lower()


def _display_path(path: Path, project_root: Path | None) -> str:
    if project_root is None:
        return path.as_posix()
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
