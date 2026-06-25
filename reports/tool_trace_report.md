# Tool Trace Report

- Trace file: `outputs/agent_trace.jsonl`
- Total tool calls: 90
- High-risk answers: 0

## Tool Call Counts

- check_order_state: 7
- check_usage_state: 9
- check_user_state: 9
- classify_issue: 20
- read_policy: 18
- risk_check: 20
- search_docs: 7

## Required Tool Coverage

- Required tools total: 38
- Available required tools: 37
- Future mock unavailable tools: 1
- Not applicable tools: 0
- Future tools are visible in reports but excluded from strict `tool_call_accuracy`.
- Phase 3.6 local mock business-state tools are included in available-tool tracing and scoring.

## Future Tool Tasks

- product_009: check_risk_state

## Trace Format

`agent_trace.jsonl` stores one JSON object per event with `trace_id`, `task_id`, `agent`, `provider`, `event_type`, `payload`, and `timestamp`.

## Debugging Value

Tracing makes it possible to inspect task starts, retrieval, tool calls, risk checks, final answers, task ends, and errors without changing the agent code.

## Current Tool Coverage Limitations

- The MVP uses local mock tools only.
- Order and usage checks use local mock data, not real business systems.
- Payment, invoice, and deeper risk-state checks remain future mock unavailable tools.
- A reasonable substitute tool call is shown in `tool_calls`, but it is not treated as a full hit for a distinct future tool.
