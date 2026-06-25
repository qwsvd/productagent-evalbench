# Baidu Agent Engineer JD Alignment

## Agent Implementation, Optimization, Performance Evaluation

The project implements BaselineAgent, RagAgent, ToolAgent, and EvaluatorAgent. It measures heuristic answer success, tool accuracy, risk, context usage, user experience, latency, cost, token estimates, and error rates.

## Context Engineering

RAG top_k experiments compare narrow and broader retrieved context. Reports explain how retrieved context is constructed and how context size affects recall, cost, and grounding.

## Experiments And Tests

`python -m productagent.cli experiments` generates experiment matrix, optimization, ablation, context engineering, and evaluator reports. `regression-check` verifies key benchmark invariants.

## Single-Agent And Multi-Agent Framework Understanding

ToolAgent is the primary single-agent workflow. EvaluatorAgent is a minimal offline critic, representing a small multi-agent evaluation pattern without adding a heavy framework.

## Modules And Tools For Agent Landing

Local tools model policy reading, retrieval, user state, order state, usage state, risk state, ticket creation, and risk checking. SkillRegistry adds metadata for tool selection.

## Agent Research Awareness

Docs discuss RAG, Memory, Skills, MCP-style tool interfaces, model provider abstraction, provider eval isolation, and cost/latency/error tracking.

## RAG / Memory / Skill / MCP

RAG uses local docs. Memory is optional session memory. Skills are registered in SkillRegistry. MCP-style local JSON-RPC supports tool discovery and invocation.

## GPT / Claude / Gemini / Open Models

Provider layer supports OpenAI, Claude, Gemini, DeepSeek, and Qwen, while default tests use MockProvider.

## Mainstream Agent Framework Understanding

The project intentionally avoids LangChain, LlamaIndex, vector databases, and heavy frameworks to make the core engineering boundaries explicit.

## Programming Ability

The codebase includes CLI, schemas, JSONL outputs, tracing, cost/performance aggregation, CI, smoke tests, and pytest coverage.
