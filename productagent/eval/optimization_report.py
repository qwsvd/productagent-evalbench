from typing import Any


def build_optimization_report(experiment_summaries: list[dict[str, Any]]) -> str:
    lines = [
        "# Optimization Report",
        "",
        "## Baseline to RAG",
        "",
        "RAG adds retrieved product context, improving inspectability and grounding compared with pure provider prompting.",
        "",
        "## RAG to ToolAgent",
        "",
        "ToolAgent adds issue classification, local state checks, risk checks, route_reason, and structured tool_calls.",
        "",
        "## ToolAgent to ToolAgent + Memory",
        "",
        "Session memory can reuse recent local task context, but it is disabled by default to keep mock benchmarks reproducible.",
        "",
        "## top_k=1 vs top_k=3",
        "",
        "`top_k=1` is smaller and cheaper. `top_k=3` usually increases recall and context_usage_score, but may add irrelevant context.",
        "",
        "## Experiment Summary",
        "",
        "| Variant | Agent | top_k | Memory | Avg Tool Accuracy | Avg Risk | Avg UX |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for item in experiment_summaries:
        lines.append(
            "| {name} | {agent} | {top_k} | {memory_mode} | {tool_accuracy:.3f} | {risk:.3f} | {ux:.3f} |".format(
                name=item["name"],
                agent=item["agent"],
                top_k=item["top_k"],
                memory_mode=item["memory_mode"],
                tool_accuracy=item["avg_tool_call_accuracy"],
                risk=item["avg_hallucination_risk"],
                ux=item["avg_user_experience_score"],
            )
        )
    lines.extend(
        [
            "",
            "## Current Failure Cases",
            "",
            "Current failures are mostly heuristic gaps: mock provider wording, keyword retrieval limits, and encoded legacy Chinese text handling.",
            "",
            "## No Real-Model Fabrication",
            "",
            "This optimization report uses mock/local runs only and does not claim real DeepSeek/Qwen/OpenAI/Gemini/Claude performance.",
            "",
        ]
    )
    return "\n".join(lines)


def build_ablation_report(experiment_summaries: list[dict[str, Any]]) -> str:
    lines = [
        "# Ablation Report",
        "",
        "This ablation compares retrieval, tool use, session memory, skill metadata, and MCP-style catalog availability under mock evaluation.",
        "",
    ]
    for item in experiment_summaries:
        lines.append(
            f"- {item['name']}: agent={item['agent']}, top_k={item['top_k']}, memory={item['memory_mode']}, skills={item['skills']}, mcp_catalog={item['mcp_catalog']}"
        )
    lines.extend(
        [
            "",
            "Interpretation: ablation results are local engineering signals, not real-model benchmarks.",
            "",
        ]
    )
    return "\n".join(lines)
