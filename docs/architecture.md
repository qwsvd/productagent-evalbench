# Architecture

## Components

- Agents: `BaselineAgent`, `RagAgent`, `ToolAgent`, and offline `EvaluatorAgent`.
- Providers: `MockProvider`, `DeepSeekProvider`, `QwenProvider`, `OpenAIProvider`, `GeminiProvider`, `ClaudeProvider`.
- Retrieval: local keyword retriever over `data/product_docs/`.
- Tools: local mock product, policy, user, order, usage, risk, ticket, and risk-check tools.
- Memory: optional in-process `SessionMemoryStore`.
- Skills: `SkillRegistry` metadata layer over local tools.
- MCP-style interface: local JSON-RPC style `initialize`, `tools/list`, and `tools/call`.
- Eval: heuristic metrics, experiment matrix, ablation reports, regression check.
- Benchmark: dry-run default model benchmark with cost, latency, token, and error tracking.

## Data Flow

Task JSONL -> Agent -> optional retrieval/tools/memory -> Provider -> structured result -> trace JSONL -> eval metrics -> reports.

## Safety Boundary

Default runs are local and offline. External provider calls require explicit `--real-run`, API keys, budget, max task count, and max output tokens.
