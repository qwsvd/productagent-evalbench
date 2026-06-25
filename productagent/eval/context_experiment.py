from typing import Any


def build_experiment_matrix() -> list[dict[str, Any]]:
    return [
        {"name": "baseline_mock", "agent": "baseline", "provider": "mock", "top_k": 0, "memory_mode": "off", "skills": False, "mcp_catalog": False},
        {"name": "rag_top_k_1", "agent": "rag", "provider": "mock", "top_k": 1, "memory_mode": "off", "skills": False, "mcp_catalog": False},
        {"name": "rag_top_k_3", "agent": "rag", "provider": "mock", "top_k": 3, "memory_mode": "off", "skills": False, "mcp_catalog": False},
        {"name": "tool_without_memory", "agent": "tool", "provider": "mock", "top_k": 3, "memory_mode": "off", "skills": True, "mcp_catalog": False},
        {"name": "tool_with_memory_session", "agent": "tool", "provider": "mock", "top_k": 3, "memory_mode": "session", "skills": True, "mcp_catalog": False},
        {"name": "tool_with_skills", "agent": "tool", "provider": "mock", "top_k": 3, "memory_mode": "off", "skills": True, "mcp_catalog": False},
        {"name": "tool_with_mcp_catalog", "agent": "tool", "provider": "mock", "top_k": 3, "memory_mode": "off", "skills": True, "mcp_catalog": True},
    ]


def build_context_engineering_report() -> str:
    return "\n".join(
        [
            "# Context Engineering Report",
            "",
            "## Retrieved Context Construction",
            "",
            "`RagAgent` and `ToolAgent` build context from local Markdown documents and local tool outputs. `retrieved_context` contains source file, chunk id, content, and score.",
            "",
            "## top_k Impact",
            "",
            "`top_k=1` keeps context narrow and easier to inspect, but may miss policy details. `top_k=3` improves recall, but can include extra context that makes answer grounding harder to audit.",
            "",
            "## context_usage_score",
            "",
            "`context_usage_score` is a heuristic: RAG or ToolAgent gets credit when retrieved context or policy/search tool context exists. Baseline stays at 0.",
            "",
            "## Risks",
            "",
            "- Too little context can miss expected answer points.",
            "- Too much context can distract answer generation and increase cost in real-provider runs.",
            "",
            "## Why No Vector Database",
            "",
            "This benchmark intentionally avoids vector databases so it remains lightweight, local, reproducible, and dependency-minimal.",
            "",
            "## Future Vector Retrieval",
            "",
            "A future phase can add embedding-based retrieval behind the same retriever interface and compare it against keyword retrieval with the same experiment matrix.",
            "",
        ]
    )
