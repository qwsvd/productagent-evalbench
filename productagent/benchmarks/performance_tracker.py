from collections import Counter, defaultdict
from typing import Any


def summarize_performance(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[(record.get("provider", "unknown"), record.get("agent", "unknown"))].append(record)

    summaries = []
    for (provider, agent), items in sorted(grouped.items()):
        statuses = Counter(item.get("status", "unknown") for item in items)
        errors = Counter(item.get("error_code") for item in items if item.get("error_code"))
        latencies = [item.get("latency_ms") for item in items if isinstance(item.get("latency_ms"), (int, float))]
        costs = [item.get("estimated_cost_usd") for item in items if isinstance(item.get("estimated_cost_usd"), (int, float))]
        summaries.append(
            {
                "provider": provider,
                "agent": agent,
                "tasks_run": len(items),
                "success_count": statuses.get("ok", 0),
                "error_count": len(items) - statuses.get("ok", 0),
                "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
                "estimated_cost_usd": round(sum(costs), 6) if costs else 0.0,
                "provider_not_configured_count": errors.get("provider_not_configured", 0),
                "timeout_count": errors.get("provider_timeout", 0),
                "status_distribution": dict(statuses),
                "notes": "Dry-run and mock records are not real model performance.",
            }
        )
    return summaries


def build_performance_report(records: list[dict[str, Any]]) -> str:
    rows = summarize_performance(records)
    lines = [
        "# Model Performance Comparison",
        "",
        "| Provider | Agent | Tasks | Success | Errors | Avg Latency ms | Estimated Cost USD | Notes |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {provider} | {agent} | {tasks_run} | {success_count} | {error_count} | {latency} | {cost:.6f} | {notes} |".format(
                provider=row["provider"],
                agent=row["agent"],
                tasks_run=row["tasks_run"],
                success_count=row["success_count"],
                error_count=row["error_count"],
                latency=row["avg_latency_ms"] if row["avg_latency_ms"] is not None else "",
                cost=row["estimated_cost_usd"],
                notes=row["notes"],
            )
        )
    return "\n".join(lines) + "\n"
