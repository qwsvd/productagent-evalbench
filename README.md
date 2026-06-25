# ProductAgent-EvalBench

## Phase 3: Tools + Tracing + Eval

`ToolAgent` is the third MVP agent. It classifies each task, calls local mock tools when useful, records trace events, runs a local risk check, and then uses `MockProvider` for the final answer. It does not call real APIs, real databases, LangChain, LlamaIndex, vector databases, or online model providers.

### Local Tools

- `search_docs(query, top_k=3)`: reuses the existing keyword retriever over `data/product_docs/`.
- `read_policy(policy_name)`: reads `refund_policy`, `account_policy`, `risk_rules`, `feature_guide`, or `faq`.
- `check_user_state(user_id, feature_name=None)`: returns deterministic mock states for `user_001` through `user_004`.
- `classify_issue(user_query)`: classifies refund, membership, account, payment, invoice, complaint, product question, or unknown issues.
- `create_ticket(user_id, issue_type, summary)`: creates a deterministic mock ticket.
- `risk_check(answer_or_plan)`: flags risky promises such as direct refunds, direct unblocks, fabricated user state, password requests, and uncertain claims without verification.

### Tracing

Agent runs write JSONL traces to:

```text
outputs/agent_trace.jsonl
```

Trace events include `task_start`, `retrieval`, `tool_call`, `risk_check`, `final_answer`, `task_end`, and `error`. Each event includes `trace_id`, `task_id`, `agent`, `provider`, `event_type`, `payload`, and `timestamp`.

### Eval Metrics

The MVP eval module computes heuristic local scores only:

- `task_success_score`
- `tool_call_accuracy`
- `hallucination_risk`
- `context_usage_score`
- `user_experience_score`

### Run ToolAgent

```bash
python -m productagent.cli run --agent tool --provider mock --task-set product_tasks
```

Output:

```text
outputs/tool_mock_results.jsonl
outputs/agent_trace.jsonl
```

### Compare Baseline vs RAG vs Tool

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

### Tool Coverage and Eval Fairness

`ToolAgent` uses local mock tools only. The task set separates required tools into `available`, `future_mock_unavailable`, and `not_applicable` through the `tool_availability` field.

Eval only applies strict `tool_call_accuracy` scoring to tools marked `available`. `future_mock_unavailable` means the tool is reasonable in a real product system, but the current offline MVP intentionally does not implement it. This avoids treating a future integration gap, such as order-state or usage-state lookup, as a current Agent tool-selection error.

For details, see:

```text
docs/tool_coverage.md
```

## Phase 3.6: Tool Routing and Mock Business-State Tools

Phase 3.6 fixes ToolAgent routing for product feature questions. Product and feature queries now prioritize `search_docs`, so feature-guide tasks are evaluated against the local product docs instead of being misrouted as only membership checks.

This phase also adds two local mock business-state tools:

- `check_order_state`: returns deterministic mock order/payment/refundability state.
- `check_usage_state`: returns deterministic mock feature usage and quota state.

These tools do not connect to a real order system, user system, database, or external API. They are small local fixtures used to make tool calling, tracing, eval, and fair tool coverage reproducible in the offline MVP.

Eval now treats `check_order_state` and `check_usage_state` as `available` tools for strict `tool_call_accuracy`. Future integrations such as payment-state, invoice-state, and deeper risk-state checks remain `future_mock_unavailable`.

The project goal remains Agent engineering evaluation: tool calls, tracing, heuristic eval, and fair tool coverage reporting. It does not pretend to provide production business-system access.

### Phase 3 Limitations

1. User state is mock data.
2. Tools are local simulations.
3. Eval metrics are heuristic and do not represent production online evaluation.
4. No real model provider or real database is connected.

ProductAgent-EvalBench 是一个面向产品知识库与用户任务的多模型 Agent 上下文工程与评测系统。

## 项目定位

本项目不是普通聊天机器人。它关注的是：在明确的产品文档、任务类型、预期要点和风险约束下，验证 Agent 是否能稳定地产生可检查的结构化结果。

普通聊天机器人主要追求即时对话体验；ProductAgent-EvalBench 更关注产品场景中的上下文工程、检索证据、风险边界和可评测输出。

## 当前支持的 Agent

### Baseline Agent

`BaselineAgent` 是最小基线 Agent。它不检索产品文档，只把任务字段传给 `MockProvider`，用于提供一个稳定的离线对照组。

### RAG Agent

`RagAgent` 会读取 `data/product_docs/` 下的 Markdown 产品文档，使用简单关键词检索找到相关文档片段，并把这些片段作为 `retrieved_context` 注入给 `MockProvider`。

RAG Agent 仍然不是普通聊天机器人：它的目标不是自由聊天，而是让答案能引用产品知识库上下文，并保留任务评测需要的结构化字段。

## 当前 MVP 支持什么

- 离线运行，不依赖真实模型 API。
- 内置 `MockProvider`，返回稳定的模拟答案。
- 支持 `BaselineAgent` 和 `RagAgent`。
- 提供 5 份模拟产品文档。
- 提供 20 条产品任务，覆盖产品问答、退款规则、会员权益、账号限制、问题分类和风险控制。
- 提供命令行入口批量运行任务。
- 支持 baseline vs rag 简单对比报告。
- 将完整运行结果写入 `outputs/`，将对比报告写入 `reports/`。

## 安装

建议先安装测试依赖：

```bash
python -m pip install -e ".[dev]"
```

## 运行 Baseline

```bash
python -m productagent.cli run --agent baseline --provider mock --task-set product_tasks
```

输出文件：

```text
outputs/baseline_mock_results.jsonl
```

## 运行 RAG

```bash
python -m productagent.cli run --agent rag --provider mock --task-set product_tasks
```

输出文件：

```text
outputs/rag_mock_results.jsonl
```

RAG 输出中会额外包含：

- `retrieved_context`
- 每个检索片段的 `source_file`
- 每个检索片段的 `chunk_id`
- 每个检索片段的 `content`
- 每个检索片段的 `score`

## 运行 Baseline vs RAG 对比

```bash
python -m productagent.cli compare --agents baseline,rag --provider mock --task-set product_tasks
```

该命令会生成：

```text
outputs/baseline_mock_results.jsonl
outputs/rag_mock_results.jsonl
reports/rag_comparison.md
```

## 运行测试

```bash
python -m pytest -q
```

## 当前局限

- RAG 只是关键词检索，不是向量数据库。
- 没有使用 LangChain、LlamaIndex 或任何复杂框架。
- 没有联网，不需要 API Key。
- `MockProvider` 只模拟稳定答案，不代表真实模型能力。
- 还没有 Memory、Tools、Tracing 和自动评分系统。
- 当前结果适合教学和本地验证，不代表真实线上系统效果。

## 下一阶段计划

- RAG：改进 chunk 策略、召回策略和引用格式。
- Memory：记录历史任务和用户上下文，支持连续任务。
- Tools：实现可插拔工具接口，例如读取用户状态、查询订单和读取政策。
- Tracing：记录每一步上下文、工具调用和 Provider 输入输出。
- Eval：加入自动评分、人工审查字段和多模型对比报表。
