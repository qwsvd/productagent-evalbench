from typing import Any

from productagent.eval.metrics import evaluate_result


def evaluate_agent_results(
    agent_name: str,
    results: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    tasks_by_id = {task["task_id"]: task for task in tasks}
    evaluated: list[dict[str, Any]] = []

    for result in results:
        task = tasks_by_id.get(result["task_id"], {})
        metrics = evaluate_result(result, task)
        evaluated.append(
            {
                "agent": agent_name,
                "task_id": result["task_id"],
                "metrics": metrics,
                "result": result,
                "task": task,
            }
        )
    return evaluated


def evaluate_results_by_agent(
    results_by_agent: dict[str, list[dict[str, Any]]],
    tasks: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    return {
        agent_name: evaluate_agent_results(agent_name, results, tasks)
        for agent_name, results in results_by_agent.items()
    }
