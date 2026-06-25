import json
from collections import Counter
from pathlib import Path
from typing import Any


def build_eval_summary(
    evaluated_by_agent: dict[str, list[dict[str, Any]]],
    output_paths: dict[str, Path],
    task_count: int,
    project_root: Path,
) -> str:
    lines = [
        "# Eval Summary",
        "",
        f"- Total tasks: {task_count}",
        "",
        "## Result Files",
        "",
    ]
    for agent_name, path in output_paths.items():
        lines.append(f"- {agent_name}: `{_display_path(path, project_root)}`")

    lines.extend(
        [
            "",
            "## Average Metrics",
            "",
            "| Agent | Task Success | Hallucination Risk | User Experience |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for agent_name, evaluated_items in evaluated_by_agent.items():
        lines.append(
            "| {agent} | {success:.3f} | {risk:.3f} | {ux:.3f} |".format(
                agent=agent_name,
                success=_average(evaluated_items, "task_success_score"),
                risk=_average(evaluated_items, "hallucination_risk"),
                ux=_average(evaluated_items, "user_experience_score"),
            )
        )

    lines.extend(
        [
            "",
            "## ToolAgent Improvements",
            "",
            "- Adds deterministic local tool calls before the final answer.",
            "- Records tool calls and risk checks in structured results and traces.",
            "- Uses local policy documents and mock user state instead of free-form guesses.",
            "",
            "## Current Limitations",
            "",
            "- User state is mock data only.",
            "- Tools are local simulations and do not call real systems.",
            "- Eval metrics are heuristic and are not a substitute for production evaluation.",
            "- No real model provider or real database is connected.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_failure_analysis(evaluated_by_agent: dict[str, list[dict[str, Any]]]) -> str:
    lines = ["# Failure Analysis", "", "## Low-Scoring Tasks", ""]
    low_rows: list[str] = []
    reason_counts: Counter[str] = Counter()

    for agent_name, evaluated_items in evaluated_by_agent.items():
        for item in evaluated_items:
            metrics = item["metrics"]
            reasons = _failure_reasons(metrics, item)
            if reasons:
                reason_counts.update(reasons)
            if (
                metrics["task_success_score"] < 0.67
                or metrics["hallucination_risk"] > 0
                or (metrics["tool_call_accuracy"] is not None and metrics["tool_call_accuracy"] < 1)
            ):
                low_rows.append(
                    f"- {agent_name} / {item['task_id']}: "
                    f"success={metrics['task_success_score']}, "
                    f"tool_accuracy={metrics['tool_call_accuracy']}, "
                    f"risk={metrics['hallucination_risk']}; "
                    f"reasons={', '.join(reasons) if reasons else 'none'}"
                )

    lines.extend(low_rows or ["- No low-scoring tasks found by the current heuristic."])
    lines.extend(["", "## Failure Reason Categories", ""])
    categories = [
        "retrieval_failure",
        "tool_selection_error",
        "risk_check_found_issue",
        "expected_points_not_covered",
        "mock_provider_expression_gap",
    ]
    for category in categories:
        lines.append(f"- {category}: {reason_counts.get(category, 0)}")

    lines.extend(
        [
            "",
            "## Next Improvements",
            "",
            "- Add more task metadata so required tools can match the available local tool set.",
            "- Improve keyword matching for Chinese text and legacy encoded data.",
            "- Add richer mock provider templates for tool-grounded answers.",
            "- Add targeted tests for low-scoring task categories.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_tool_trace_report(trace_path: Path, project_root: Path) -> str:
    tool_counts: Counter[str] = Counter()
    high_risk_count = 0
    total_tool_calls = 0

    if trace_path.exists():
        with trace_path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                payload = record.get("payload", {})
                if record.get("event_type") == "tool_call":
                    total_tool_calls += 1
                    tool_counts[str(payload.get("tool_name", "unknown"))] += 1
                if record.get("event_type") == "risk_check":
                    if payload.get("result", {}).get("risk_level") == "high":
                        high_risk_count += 1

    lines = [
        "# Tool Trace Report",
        "",
        f"- Trace file: `{_display_path(trace_path, project_root)}`",
        f"- Total tool calls: {total_tool_calls}",
        f"- High-risk answers: {high_risk_count}",
        "",
        "## Tool Call Counts",
        "",
    ]
    if tool_counts:
        lines.extend(f"- {tool_name}: {count}" for tool_name, count in sorted(tool_counts.items()))
    else:
        lines.append("- No tool calls recorded.")

    lines.extend(
        [
            "",
            "## Trace Format",
            "",
            "`agent_trace.jsonl` stores one JSON object per event with `trace_id`, `task_id`, `agent`, `provider`, `event_type`, `payload`, and `timestamp`.",
            "",
            "## Debugging Value",
            "",
            "Tracing makes it possible to inspect task starts, retrieval, tool calls, risk checks, final answers, task ends, and errors without changing the agent code.",
        ]
    )
    return "\n".join(lines) + "\n"


def _failure_reasons(metrics: dict[str, Any], item: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    result = item.get("result", {})
    agent = item.get("agent")

    if agent in {"rag", "tool"} and metrics["context_usage_score"] == 0:
        reasons.append("retrieval_failure")
    if metrics["tool_call_accuracy"] is not None and metrics["tool_call_accuracy"] < 1:
        reasons.append("tool_selection_error")
    if metrics["hallucination_risk"] > 0:
        reasons.append("risk_check_found_issue")
    if metrics["task_success_score"] < 1:
        reasons.append("expected_points_not_covered")
    if metrics["task_success_score"] < 1 and not result.get("retrieved_context"):
        reasons.append("mock_provider_expression_gap")
    return reasons


def _average(evaluated_items: list[dict[str, Any]], metric_name: str) -> float:
    if not evaluated_items:
        return 0.0
    values = [item["metrics"][metric_name] for item in evaluated_items]
    return sum(values) / len(values)


def _display_path(path: Path, project_root: Path) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()
