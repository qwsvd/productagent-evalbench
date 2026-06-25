# Agent Research Brief

## Practical Themes

- Tool use improves auditability when tool calls and route reasons are recorded.
- RAG improves grounding but requires context-size experiments.
- Memory can help repeated sessions but should be disabled in deterministic benchmarks.
- Skills make tool selection explainable without requiring a heavy agent framework.
- MCP-style catalogs separate discovery from invocation and can be tested locally.
- Real-provider eval must track latency, cost, error rate, token usage, and provider setup.

## Project Position

This project implements these ideas with small local modules and explicit reports. It avoids claiming production capability where only mock data exists.
