import argparse
from pathlib import Path
from typing import Any

from productagent.agents import BaselineAgent
from productagent.data_loader import PROJECT_ROOT, load_task_set
from productagent.models import MockProvider
from productagent.output_writer import write_jsonl


def build_provider(provider_name: str) -> MockProvider:
    if provider_name == "mock":
        return MockProvider()
    raise ValueError(f"Unsupported provider: {provider_name}")


def build_agent(agent_name: str, provider: MockProvider) -> BaselineAgent:
    if agent_name == "baseline":
        return BaselineAgent(provider=provider)
    raise ValueError(f"Unsupported agent: {agent_name}")


def run_task_set(
    agent_name: str,
    provider_name: str,
    task_set: str,
    output_path: str | Path | None = None,
    project_root: str | Path | None = None,
) -> list[dict[str, Any]]:
    root = Path(project_root) if project_root else PROJECT_ROOT
    provider = build_provider(provider_name)
    agent = build_agent(agent_name, provider)
    tasks = load_task_set(task_set, project_root=root)

    results = [agent.run_task(task) for task in tasks]
    final_output_path = output_path or root / "outputs" / f"{agent_name}_{provider_name}_results.jsonl"
    write_jsonl(results, final_output_path)

    print(f"Ran {len(results)} tasks with agent={agent_name}, provider={provider_name}")
    print(f"Saved results to {final_output_path}")
    for result in results:
        first_line = result["final_answer"].splitlines()[0]
        print(f"- {result['task_id']}: {first_line}")

    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ProductAgent-EvalBench MVP tasks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a task set.")
    run_parser.add_argument("--agent", default="baseline", choices=["baseline"])
    run_parser.add_argument("--provider", default="mock", choices=["mock"])
    run_parser.add_argument("--task-set", default="product_tasks")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        run_task_set(
            agent_name=args.agent,
            provider_name=args.provider,
            task_set=args.task_set,
        )
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())