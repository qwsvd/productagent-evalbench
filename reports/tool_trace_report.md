# Tool Trace Report

- Trace file: `outputs/agent_trace.jsonl`
- Total tool calls: 71
- High-risk answers: 0

## Tool Call Counts

- check_user_state: 11
- classify_issue: 20
- read_account_policy: 6
- read_faq: 2
- read_feature_guide: 5
- read_refund_policy: 5
- risk_check: 20
- search_docs: 2

## Trace Format

`agent_trace.jsonl` stores one JSON object per event with `trace_id`, `task_id`, `agent`, `provider`, `event_type`, `payload`, and `timestamp`.

## Debugging Value

Tracing makes it possible to inspect task starts, retrieval, tool calls, risk checks, final answers, task ends, and errors without changing the agent code.
