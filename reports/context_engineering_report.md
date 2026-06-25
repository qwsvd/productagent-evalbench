# Context Engineering Report

## Retrieved Context Construction

`RagAgent` and `ToolAgent` build context from local Markdown documents and local tool outputs. `retrieved_context` contains source file, chunk id, content, and score.

## top_k Impact

`top_k=1` keeps context narrow and easier to inspect, but may miss policy details. `top_k=3` improves recall, but can include extra context that makes answer grounding harder to audit.

## context_usage_score

`context_usage_score` is a heuristic: RAG or ToolAgent gets credit when retrieved context or policy/search tool context exists. Baseline stays at 0.

## Risks

- Too little context can miss expected answer points.
- Too much context can distract answer generation and increase cost in real-provider runs.

## Why No Vector Database

This benchmark intentionally avoids vector databases so it remains lightweight, local, reproducible, and dependency-minimal.

## Future Vector Retrieval

A future phase can add embedding-based retrieval behind the same retriever interface and compare it against keyword retrieval with the same experiment matrix.
