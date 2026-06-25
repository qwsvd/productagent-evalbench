# ProductAgent-EvalBench

A local, reproducible Agent evaluation bench for product-support tasks.

It compares:

- `BaselineAgent`
- `RagAgent`
- `ToolAgent`

It demonstrates:

- retrieval context
- local mock tools
- route reasoning
- tracing
- heuristic eval
- fair tool coverage scoring
- Provider abstraction for DeepSeek / Qwen / OpenAI / Gemini
- strict separation between mock eval and external-provider eval

Mock runs need no real model APIs, real databases, external services, LangChain, LlamaIndex, or vector databases.

## Quick Start

```bash
python -m pytest -q
python -m productagent.cli providers
python -m productagent.cli compare --agents baseline,rag,tool --provider mock --task-set product_tasks
```

## Current Status

- Mock eval: supported and fully offline.
- External providers: configurable but not used in default tests.
- API keys: never committed.
- Real model benchmark: not claimed unless separately run.

## Current Agents

### BaselineAgent

`BaselineAgent` sends task fields directly to `MockProvider`. It does not retrieve documents or call tools. It is the stable offline baseline.

### RagAgent

`RagAgent` reads Markdown documents from `data/product_docs/`, uses a simple keyword retriever, and injects `retrieved_context` into `MockProvider`.

### ToolAgent

`ToolAgent` classifies the issue, chooses local mock tools, records trace events, runs risk checks, and returns structured results with tool calls and routing explanations.

## Local Tools

- `search_docs(query, top_k=3)`: searches local product Markdown documents.
- `read_policy(policy_name)`: reads `refund_policy`, `account_policy`, `risk_rules`, `feature_guide`, or `faq`.
- `check_user_state(user_id, feature_name=None)`: returns deterministic mock user state.
- `check_order_state(order_id=None, user_id=None)`: returns deterministic mock order/payment/refundability state.
- `check_usage_state(user_id, feature_name=None)`: returns deterministic mock feature usage and quota state.
- `check_risk_state(user_id=None, account_id=None, order_id=None, issue_type=None)`: returns deterministic mock risk level, flags, allowed actions, and blocked actions.
- `classify_issue(user_query)`: classifies product, refund, membership, account, payment, invoice, complaint, or unknown issues.
- `create_ticket(user_id, issue_type, summary)`: creates a deterministic mock ticket.
- `risk_check(answer_or_plan)`: flags risky promises such as direct refunds, direct unblocks, fabricated user state, password requests, and uncertain claims without verification.

## Tracing

Agent runs write JSONL traces to:

```text
outputs/agent_trace.jsonl
```

Trace events include `task_start`, `retrieval`, `tool_call`, `route_decision`, `risk_check`, `final_answer`, `task_end`, and `error`. Each event includes `trace_id`, `task_id`, `agent`, `provider`, `event_type`, `payload`, and `timestamp`.

## Eval Metrics

The MVP eval module computes heuristic local scores:

- `task_success_score`
- `tool_call_accuracy`
- `hallucination_risk`
- `context_usage_score`
- `user_experience_score`

`tool_call_accuracy` only strictly scores required tools marked `available` in task metadata.

## Tool Coverage and Eval Fairness

`ToolAgent` uses local mock tools. The task set separates required tools into `available`, `future_mock_unavailable`, and `not_applicable` through the `tool_availability` field.

Eval only applies strict `tool_call_accuracy` scoring to tools marked `available`. `future_mock_unavailable` means the tool is reasonable in a real product system, but the current offline MVP intentionally does not implement it. This avoids treating a future integration gap as a current Agent tool-selection error.

See:

```text
docs/tool_coverage.md
```

## Phase 3: Tools + Tracing + Eval

Phase 3 introduced `ToolAgent`, local tools, JSONL tracing, and heuristic eval reports.

Outputs from comparison runs:

```text
outputs/baseline_mock_results.jsonl
outputs/rag_mock_results.jsonl
outputs/tool_mock_results.jsonl
outputs/agent_trace.jsonl
reports/eval_summary.md
reports/failure_analysis.md
reports/tool_trace_report.md
reports/rag_comparison.md
```

## Phase 3.6: Tool Routing and Mock Business-State Tools

Phase 3.6 fixed ToolAgent routing for product feature questions. Product and feature queries now prioritize `search_docs`.

It also added two local mock business-state tools:

- `check_order_state`
- `check_usage_state`

These tools do not connect to real order, payment, user, or database systems. Eval treats them as `available` local mock tools for strict scoring.

## Phase 3.7: Risk State Tool and Route Reason

Phase 3.7 adds:

- `check_risk_state`, a local mock risk-state tool.
- `route_reason` in ToolAgent outputs, explaining why tools were selected.
- `route_decision` trace events.
- Report updates showing risk-state tool coverage and route explainability.

This phase still does not connect to real risk-control, order, user, payment, invoice, database, or model-provider systems.

## Phase 4: OpenAI-compatible Model Providers

Phase 4 adds provider engineering structure for:

- `DeepSeekProvider`
- `QwenProvider`
- `OpenAIProvider`
- `GeminiProvider`

These providers reuse `OpenAICompatibleProvider`, a small stdlib-only chat-completions client. Default tests still use `MockProvider` and do not call real APIs. Without API keys, external providers return structured `provider_not_configured` errors instead of crashing.

Supported provider names:

```text
mock
deepseek
qwen
openai
gemini
```

Copy the environment template if you want to configure real providers:

```bash
copy .env.example .env
```

Then set environment variables in your shell or local environment manager. Do not commit `.env`.

Provider setup details are in:

```text
docs/provider_setup.md
```

### Provider Config Check

```bash
python -m productagent.cli providers
```

This prints only `available`, `configured`, or `missing_api_key`. It does not print keys and does not make network calls.

### Run With Mock

```bash
python -m productagent.cli compare --agents baseline,rag,tool --provider mock --task-set product_tasks
```

### Try DeepSeek

```bash
python -m productagent.cli run --agent tool --provider deepseek --task-set product_tasks
```

Set `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`, and `DEEPSEEK_TIMEOUT_SECONDS`. DeepSeek base URL and model should follow the latest official console or documentation.

### Try Qwen

```bash
python -m productagent.cli run --agent tool --provider qwen --task-set product_tasks
```

Set `QWEN_API_KEY`, `QWEN_BASE_URL`, `QWEN_MODEL`, and `QWEN_TIMEOUT_SECONDS`. Qwen base URL and model should follow the latest official console or documentation.

### Try OpenAI

```bash
python -m productagent.cli run --agent tool --provider openai --task-set product_tasks
```

Set `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`, and `OPENAI_TIMEOUT_SECONDS`. OpenAI model names change quickly, so set `OPENAI_MODEL` to a currently available model from the official platform.

### Try Gemini

```bash
python -m productagent.cli run --agent tool --provider gemini --task-set product_tasks
```

Set `GEMINI_API_KEY`, `GEMINI_BASE_URL`, `GEMINI_MODEL`, and `GEMINI_TIMEOUT_SECONDS`. Gemini OpenAI-compatible configuration, base URL, and model names should follow the latest official documentation or console. Phase 4 does not implement complex Gemini-specific adaptation.

### API Key Safety

- Do not commit real API keys.
- Do not send keys to the model or paste them into chats.
- Do not write keys into GitHub, README, tests, reports, outputs, or source files.
- Tests do not need keys.
- Mock provider runs the full local project without keys.

## Phase 5: Provider Evaluation Isolation and Benchmark Pack

Phase 5 adds:

- run metadata with `run_id`, `provider_mode`, `task_set`, `schema_version`, and timestamp.
- stable result schema validation for JSONL records.
- benchmark manifest generation at `reports/benchmark_manifest.json`.
- provider eval isolation reporting at `reports/provider_eval_isolation.md`.
- a reproducibility runbook at `docs/runbook.md`.

The default benchmark remains the offline mock run. External-provider runs are supported by configuration but must be evaluated and reported separately.

## Install

```bash
python -m pip install -e ".[dev]"
```

## Run Baseline

```bash
python -m productagent.cli run --agent baseline --provider mock --task-set product_tasks
```

Output:

```text
outputs/baseline_mock_results.jsonl
```

## Run RAG

```bash
python -m productagent.cli run --agent rag --provider mock --task-set product_tasks
```

Output:

```text
outputs/rag_mock_results.jsonl
```

## Run ToolAgent

```bash
python -m productagent.cli run --agent tool --provider mock --task-set product_tasks
```

Output:

```text
outputs/tool_mock_results.jsonl
outputs/agent_trace.jsonl
```

## Compare Baseline vs RAG vs Tool

```bash
python -m productagent.cli compare --agents baseline,rag,tool --provider mock --task-set product_tasks
```

Outputs:

```text
outputs/baseline_mock_results.jsonl
outputs/rag_mock_results.jsonl
outputs/tool_mock_results.jsonl
outputs/agent_trace.jsonl
reports/eval_summary.md
reports/failure_analysis.md
reports/tool_trace_report.md
reports/rag_comparison.md
```

## Run Tests

```bash
python -m pytest -q
```

## Current Limitations

- User state, order state, feature usage state, and risk state are local mock data.
- Tools are local simulations and do not represent real online customer-support, order, payment, permission, invoice, or risk-control systems.
- Eval metrics are heuristic rules for local Baseline/RAG/ToolAgent comparison and do not represent production online evaluation.
- Real providers require user-supplied API keys and current official base URL/model configuration.
- Network, cost, rate limits, provider availability, and model output format changes can affect real-provider results.
- Current eval remains heuristic and should not mix mock metrics with real-model conclusions without separate reporting.
- Production-grade retry, concurrency, caching, rate limiting, and cost control are not implemented.
- The project does not fabricate DeepSeek, Qwen, OpenAI, or Gemini quality results.
- Long-term Memory, real MCP Server integration, real multi-agent collaboration, and online deployment are not implemented.
