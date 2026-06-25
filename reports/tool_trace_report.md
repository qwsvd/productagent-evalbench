# Tool Trace Report

- Trace file: `outputs/agent_trace.jsonl`
- Total tool calls: 71
- High-risk answers: 0

## Tool Call Counts

- check_user_state: 11
- classify_issue: 20
- read_policy: 18
- risk_check: 20
- search_docs: 2

## Required Tool Coverage

- Required tools total: 38
- Available required tools: 31
- Future mock unavailable tools: 7
- Not applicable tools: 0
- Future tools are visible in reports but excluded from strict `tool_call_accuracy`.

## Future Tool Tasks

- product_003: check_order_state
- product_005: check_order_state, check_usage_state
- product_006: check_order_state
- product_007: check_order_state
- product_008: check_usage_state
- product_009: check_risk_state

## Trace Format

`agent_trace.jsonl` stores one JSON object per event with `trace_id`, `task_id`, `agent`, `provider`, `event_type`, `payload`, and `timestamp`.

## Debugging Value

Tracing makes it possible to inspect task starts, retrieval, tool calls, risk checks, final answers, task ends, and errors without changing the agent code.

## Current Tool Coverage Limitations

- The MVP uses local mock tools only.
- Order, usage, payment, invoice, and deeper risk-state checks are represented as future mock unavailable tools.
- A reasonable substitute tool call is shown in `tool_calls`, but it is not treated as a full hit for a distinct future tool.
