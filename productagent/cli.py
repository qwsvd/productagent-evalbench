import argparse
from pathlib import Path
from typing import Any

from productagent.agents import BaselineAgent, RagAgent
from productagent.data_loader import PROJECT_ROOT, load_task_set
from productagent.models import MockProvider
from productagent.output_writer import write_jsonl, write_markdown


SUPPORTED_AGENTS = {"baseline", "rag"}


def build_provider(provider_name: str) -> MockProvider:
    if provider_name == "mock":
        return MockProvider()
    raise ValueError(f"Unsupported provider: {provider_name}")


def build_agent(agent_name: str, provider: MockProvider, project_root: Path, top_k: int = 3) -> BaselineAgent | RagAgent:
    if agent_name == "baseline":
        return BaselineAgent(provider=provider)
    if agent_name == "rag":
        return RagAgent(provider=provider, docs_dir=project_root / "data" / "product_docs", top_k=top_k)
    raise ValueError(f"Unsupported agent: {agent_name}")


def run_task_set(
    agent_name: str,
    provider_name: str,
    task_set: str,
    output_path: str | Path | None = None,
    project_root: str | Path | None = None,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    root = Path(project_root) if project_root else PROJECT_ROOT
    provider = build_provider(provider_name)
    agent = build_agent(agent_name, provider, project_root=root, top_k=top_k)
    tasks = load_task_set(task_set, project_root=root)

    results = [agent.run_task(task) for task in tasks]
    final_output_path = output_path or root / "outputs" / f"{agent_name}_{provider_name}_results.jsonl"
    write_jsonl(results, final_output_path)

    print(f"Ran {len(results)} tasks with agent={agent_name}, provider={provider_name}")
    print(f"Saved results to {final_output_path}")
    for result in results:
        first_line = result["final_answer"].splitlines()[0]
        if agent_name == "rag":
            context_count = len(result.get("retrieved_context", []))
            print(f"- {result['task_id']}: {first_line} retrieved_context={context_count}")
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
    normalized_agents = [_normalize_agent_name(agent_name) for agent_name in agent_names]
    for agent_name in normalized_agents:
        if agent_name not in SUPPORTED_AGENTS:
            raise ValueError(f"Unsupported agent in compare: {agent_name}")

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
        )
        output_paths[agent_name] = output_path

    report = build_comparison_report(results_by_agent, output_paths, project_root=root)
    report_path = root / "reports" / "rag_comparison.md"
    write_markdown(report, report_path)
    print(f"Saved comparison report to {report_path}")
    return report_path


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
    used_docs_text = "\n".join(f"- {doc}" for doc in used_docs) if used_docs else "- 暂无检索命中文档"

    return "\n".join(
        [
            "# RAG Comparison Report",
            "",
            f"- 任务总数：{task_count}",
            f"- Baseline 输出文件：`{baseline_path}`",
            f"- RAG 输出文件：`{rag_path}`",
            "",
            "## RAG 使用了哪些文档",
            "",
            used_docs_text,
            "",
            "## RAG 相比 Baseline 的改进点",
            "",
            "- RAG 会先检索产品文档，再把相关片段注入 Provider。",
            "- RAG 结果包含 `retrieved_context`，更方便检查答案参考了哪些文档。",
            "- 对退款、会员权益、账号限制等问题，RAG 能把回答边界收敛到产品政策上下文。",
            "",
            "## 当前局限性",
            "",
            "- 当前只是关键词检索，不是向量数据库。",
            "- 当前 `MockProvider` 不代表真实模型能力。",
            "- 当前没有 Memory、真实工具调用、Tracing 或自动评分。",
            "- 检索结果只做简单打分，可能遗漏同义表达或复杂语义关系。",
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
