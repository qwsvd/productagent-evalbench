import json
from collections import Counter
from pathlib import Path
from typing import Any

from productagent.tool_coverage import split_required_tools


def build_eval_summary(
    evaluated_by_agent: dict[str, list[dict[str, Any]]],
    output_paths: dict[str, Path],
    task_count: int,
    project_root: Path,
) -> str:
    coverage = _coverage_summary(evaluated_by_agent)
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
            "## Tool Coverage Fairness",
            "",
            f"- Required tools total: {coverage['required_tools_total']}",
            f"- Available required tools: {coverage['available_required_tools_total']}",
            f"- Future mock unavailable tools: {coverage['future_mock_unavailable_total']}",
            f"- Not applicable tools: {coverage['not_applicable_total']}",
            "- Strict `tool_call_accuracy` only scores tools marked `available`.",
            "- `future_mock_unavailable` tools are reasonable future product integrations, so they are reported but excluded from strict scoring.",
            "- Phase 3.6 adds `check_order_state` and `check_usage_state` as local mock business-state tools, so they now count as available tools.",
            "- Phase 3.7 adds `check_risk_state` as a local mock risk-state tool, so risk-state requirements now count as available tools.",
            "- These mock tools do not connect to a real order system, user system, database, or external API.",
            "- `route_reason` explains why ToolAgent selected each tool, improving routing auditability.",
            "- Phase 4 adds DeepSeek, Qwen, OpenAI, and Gemini provider-layer support through `OpenAICompatibleProvider`.",
            "- This report does not fabricate real-model effects. Mock metrics and real-provider metrics should be reviewed separately.",
            "",
            "## Available Tool Hits",
            "",
            "| Agent | Available Hits | Available Total | Strict Tool Accuracy |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    lines.extend(_agent_tool_hit_rows(evaluated_by_agent))

    lines.extend(["", "## Future Tool Tasks", ""])
    lines.extend(_format_future_tasks(coverage))

    lines.extend(
        [
            "",
            "## ToolAgent Improvements",
            "",
            "- Adds deterministic local tool calls before the final answer.",
            "- Records tool calls and risk checks in structured results and traces.",
            "- Uses local policy documents and mock user state instead of free-form guesses.",
            "- Phase 3.6 improves feature-question routing through `search_docs` and adds local mock order/usage checks.",
            "- Phase 3.7 adds mock risk-state checks and `route_reason` for tool-selection explainability.",
            "- Phase 4 adds a real-provider engineering layer while keeping mock runs reproducible by default.",
            "",
            "## Current Limitations",
            "",
            "- User state is mock data only.",
            "- Tools are local simulations and do not call real systems.",
            "- Order and usage state are small local mock datasets, not production system integrations.",
            "- Risk state is also local mock data, not a production risk-control system.",
            "- Eval metrics are heuristic and are not a substitute for production evaluation.",
            "- Real providers require user-supplied API keys and current official provider configuration.",
            "- Real-model results should be generated separately and not mixed with mock-provider conclusions.",
            "- No real database is connected.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_failure_analysis(evaluated_by_agent: dict[str, list[dict[str, Any]]]) -> str:
    coverage = _coverage_summary(evaluated_by_agent)
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
    lines.extend(
        [
            "",
            "## Tool Availability Notes",
            "",
            "- `tool_selection_error` now means an agent missed a required tool marked `available`.",
            "- `future_mock_unavailable` tools are not counted as strict failures because the MVP intentionally does not implement those integrations.",
            "- `check_order_state` and `check_usage_state` are now available local mock tools and are included in strict scoring.",
            "- `check_risk_state` is now an available local mock tool and is included in strict scoring.",
            "- `route_reason` helps identify whether a low score came from routing, unavailable state, or answer wording.",
            "- Unknown risk state is handled as mock `found: false`; it should prompt verification, not a production conclusion.",
            "- Phase 4 provider support does not change mock-based failure conclusions or claim real-model quality.",
            "",
            "## Tasks With Future Tools",
            "",
        ]
    )
    lines.extend(_format_future_tasks(coverage))
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
            "- Use `route_reason` to compare expected routing against actual selected tools.",
            "- Run real-provider evaluations separately from mock reports after explicit provider configuration.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_tool_trace_report(
    trace_path: Path,
    project_root: Path,
    evaluated_by_agent: dict[str, list[dict[str, Any]]] | None = None,
) -> str:
    tool_counts: Counter[str] = Counter()
    high_risk_count = 0
    total_tool_calls = 0
    route_decision_count = 0

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
                if record.get("event_type") == "route_decision":
                    route_decision_count += 1
                if record.get("event_type") == "risk_check":
                    if payload.get("result", {}).get("risk_level") == "high":
                        high_risk_count += 1

    lines = [
        "# Tool Trace Report",
        "",
        f"- Trace file: `{_display_path(trace_path, project_root)}`",
        f"- Total tool calls: {total_tool_calls}",
        f"- High-risk answers: {high_risk_count}",
        f"- Route decision events: {route_decision_count}",
        "",
        "## Tool Call Counts",
        "",
    ]
    if tool_counts:
        lines.extend(f"- {tool_name}: {count}" for tool_name, count in sorted(tool_counts.items()))
    else:
        lines.append("- No tool calls recorded.")

    if evaluated_by_agent is not None:
        coverage = _coverage_summary(evaluated_by_agent)
        lines.extend(
            [
                "",
                "## Required Tool Coverage",
                "",
                f"- Required tools total: {coverage['required_tools_total']}",
                f"- Available required tools: {coverage['available_required_tools_total']}",
                f"- Future mock unavailable tools: {coverage['future_mock_unavailable_total']}",
                f"- Not applicable tools: {coverage['not_applicable_total']}",
                "- Future tools are visible in reports but excluded from strict `tool_call_accuracy`.",
                "- Phase 3.6 local mock business-state tools are included in available-tool tracing and scoring.",
                "- Phase 3.7 local mock risk-state tools are included in available-tool tracing and scoring.",
                "- Phase 4 provider-layer support is available, but this report does not claim real-model performance unless those providers are explicitly run.",
                "",
                "## Future Tool Tasks",
                "",
            ]
        )
        lines.extend(_format_future_tasks(coverage))

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
            "`route_decision` events show the routed issue type, selected tools, and route summary, which helps debug tool selection separately from answer quality.",
            "",
            "## Current Tool Coverage Limitations",
            "",
            "- The MVP uses local mock tools only.",
            "- Order and usage checks use local mock data, not real business systems.",
            "- Risk-state checks use local mock data, not a real risk-control system.",
            "- Payment and invoice-specific external checks remain future tool candidates.",
            "- A reasonable substitute tool call is shown in `tool_calls`, but it is not treated as a full hit for a distinct future tool.",
            "- DeepSeek, Qwen, OpenAI, and Gemini provider outputs should be traced and evaluated in separate runs, not inferred from mock results.",
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


def _coverage_summary(evaluated_by_agent: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    tasks_by_id: dict[str, dict[str, Any]] = {}
    for evaluated_items in evaluated_by_agent.values():
        for item in evaluated_items:
            task = item.get("task", {})
            task_id = task.get("task_id") or item.get("task_id")
            if task_id and task_id not in tasks_by_id:
                tasks_by_id[str(task_id)] = task

    summary: dict[str, Any] = {
        "required_tools_total": 0,
        "available_required_tools_total": 0,
        "future_mock_unavailable_total": 0,
        "not_applicable_total": 0,
        "future_tasks": [],
    }
    for task_id, task in sorted(tasks_by_id.items()):
        required_tools = task.get("required_tools", []) or []
        split = split_required_tools(required_tools, task.get("tool_availability"))
        summary["required_tools_total"] += len(required_tools)
        summary["available_required_tools_total"] += len(split["available"])
        summary["future_mock_unavailable_total"] += len(split["future_mock_unavailable"])
        summary["not_applicable_total"] += len(split["not_applicable"])
        if split["future_mock_unavailable"]:
            summary["future_tasks"].append(
                {
                    "task_id": task_id,
                    "tools": split["future_mock_unavailable"],
                }
            )
    return summary


def _agent_tool_hit_rows(evaluated_by_agent: dict[str, list[dict[str, Any]]]) -> list[str]:
    rows: list[str] = []
    for agent_name, evaluated_items in evaluated_by_agent.items():
        hit_count = sum(item["metrics"].get("available_tool_hit_count", 0) for item in evaluated_items)
        total = sum(item["metrics"].get("available_tool_total", 0) for item in evaluated_items)
        accuracy = hit_count / total if total else 0
        rows.append(f"| {agent_name} | {hit_count} | {total} | {accuracy:.3f} |")
    return rows


def _format_future_tasks(coverage: dict[str, Any]) -> list[str]:
    future_tasks = coverage.get("future_tasks", [])
    if not future_tasks:
        return ["- No tasks contain future mock unavailable tools."]
    return [
        f"- {item['task_id']}: {', '.join(item['tools'])}"
        for item in future_tasks
    ]


def _display_path(path: Path, project_root: Path) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()
