# Optimization Report

## Baseline to RAG

RAG adds retrieved product context, improving inspectability and grounding compared with pure provider prompting.

## RAG to ToolAgent

ToolAgent adds issue classification, local state checks, risk checks, route_reason, and structured tool_calls.

## ToolAgent to ToolAgent + Memory

Session memory can reuse recent local task context, but it is disabled by default to keep mock benchmarks reproducible.

## top_k=1 vs top_k=3

`top_k=1` is smaller and cheaper. `top_k=3` usually increases recall and context_usage_score, but may add irrelevant context.

## Experiment Summary

| Variant | Agent | top_k | Memory | Avg Tool Accuracy | Avg Risk | Avg UX |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| baseline_mock | baseline | 0 | off | 0.000 | 0.000 | 1.000 |
| rag_top_k_1 | rag | 1 | off | 0.000 | 0.000 | 1.000 |
| rag_top_k_3 | rag | 3 | off | 0.000 | 0.000 | 1.000 |
| tool_without_memory | tool | 3 | off | 1.000 | 0.000 | 1.000 |
| tool_with_memory_session | tool | 3 | session | 1.000 | 0.000 | 1.000 |
| tool_with_skills | tool | 3 | off | 1.000 | 0.000 | 1.000 |
| tool_with_mcp_catalog | tool | 3 | off | 1.000 | 0.000 | 1.000 |

## Current Failure Cases

Current failures are mostly heuristic gaps: mock provider wording, keyword retrieval limits, and encoded legacy Chinese text handling.

## No Real-Model Fabrication

This optimization report uses mock/local runs only and does not claim real DeepSeek/Qwen/OpenAI/Gemini/Claude performance.
