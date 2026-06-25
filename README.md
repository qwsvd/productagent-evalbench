# ProductAgent-EvalBench

ProductAgent-EvalBench is a local MVP eval bench for product-support agents. It compares a baseline agent, a RAG agent, and a tool-using agent on a fixed product task set without real model APIs, real databases, external services, LangChain, LlamaIndex, or vector databases.

The project focuses on agent engineering signals: retrieval context, local tool calls, tracing, heuristic eval, and fair tool coverage reporting.

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
- Real model APIs are not connected, including DeepSeek, Qwen, GPT, Claude, and Gemini.
- Long-term Memory, real MCP Server integration, real multi-agent collaboration, and online deployment are not implemented.
