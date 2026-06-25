# Ablation Report

This ablation compares retrieval, tool use, session memory, skill metadata, and MCP-style catalog availability under mock evaluation.

- baseline_mock: agent=baseline, top_k=0, memory=off, skills=False, mcp_catalog=False
- rag_top_k_1: agent=rag, top_k=1, memory=off, skills=False, mcp_catalog=False
- rag_top_k_3: agent=rag, top_k=3, memory=off, skills=False, mcp_catalog=False
- tool_without_memory: agent=tool, top_k=3, memory=off, skills=True, mcp_catalog=False
- tool_with_memory_session: agent=tool, top_k=3, memory=session, skills=True, mcp_catalog=False
- tool_with_skills: agent=tool, top_k=3, memory=off, skills=True, mcp_catalog=False
- tool_with_mcp_catalog: agent=tool, top_k=3, memory=off, skills=True, mcp_catalog=True

Interpretation: ablation results are local engineering signals, not real-model benchmarks.
