# Tool Coverage

## Implemented Tools

- `search_docs`: Searches local product Markdown documents through the existing keyword retriever.
- `read_policy`: Reads one supported local policy document from `data/product_docs/`.
- `check_user_state`: Returns deterministic mock user state for a small built-in user set.
- `check_order_state`: Returns deterministic local mock order state for a small built-in order set.
- `check_usage_state`: Returns deterministic local mock feature usage state for a small built-in usage set.
- `check_risk_state`: Returns deterministic local mock risk state and allowed/blocked actions.
- `classify_issue`: Classifies a user query with simple keyword rules.
- `create_ticket`: Creates a deterministic mock ticket record.
- `risk_check`: Checks an answer or plan for high-risk promises.

## Local Mock Business-State Tools

`check_order_state`, `check_usage_state`, and `check_risk_state` are local mock tools. They do not connect to a real order system, user system, risk-control system, database, or external API.

`check_order_state` can return mock payment and refundability fields for `order_001`, `order_002`, and `order_003`. Unknown orders return `found: false` and a verification note.

`check_usage_state` can return mock feature usage state for `user_001`, `user_002`, and `user_003` on `advanced_export`. Unknown users or features return `found: false` and a verification note.

`check_risk_state` can return mock risk levels, flags, allowed actions, and blocked actions for `user_001`, `user_002`, and `user_003`. Unknown users return `found: false`, `risk_level: unknown`, and a verification note.

The project implements these minimal mock versions first so ToolAgent routing, tracing, and eval can be tested locally without pretending to have production business-system access.

## Future Mock Unavailable Tools

- `check_payment_state`
- `check_invoice_state`

These tools remain reasonable for a future product support agent, but this MVP still does not connect to payment systems, invoice systems, databases, or external APIs.

## Why Not Implement Every Tool In The MVP

The current project is an offline eval bench. Its goal is to test task flow, local tool selection, tracing, and heuristic evaluation without API keys or production systems. Implementing full payment and invoice checks would require mock schemas and business logic that are larger than this stage.

## `tool_availability`

Each task can mark required tools with:

- `available`: The tool exists in the current local MVP tool set and is included in strict `tool_call_accuracy`.
- `future_mock_unavailable`: The tool is reasonable for a future product system but intentionally unavailable in this MVP. It is reported, but not counted as a strict miss.
- `not_applicable`: The tool is not reasonable for the task or should not be used. It is excluded from strict scoring.

Example:

```json
{
  "required_tools": ["read_policy", "check_order_state"],
  "tool_availability": {
    "read_policy": "available",
    "check_order_state": "available"
  }
}
```

## Eval Handling

`tool_call_accuracy` only scores required tools marked `available`.

Because `check_order_state`, `check_usage_state`, and `check_risk_state` are implemented as local mock tools, tasks requiring them count those tools in strict scoring.

`future_mock_unavailable` tools remain visible in reports so reviewers can see capability gaps, but they do not lower strict tool accuracy. This prevents a future integration gap from being mistaken for a current ToolAgent selection error.

If ToolAgent calls a reasonable substitute, such as `search_docs` or `read_policy`, that call remains visible in `tool_calls` and traces. It is not treated as a full hit for a distinct future tool such as `check_payment_state`.

## Route Reason

ToolAgent returns `route_reason` with the routed `issue_type`, selected tools, and non-selected tools. The same decision is written to tracing as a `route_decision` event.

`route_reason` helps evaluate whether ToolAgent chose the right tools before judging answer wording. For example, a refund route should show policy, order-state, risk-state, and final risk-check reasoning instead of only showing the final answer.

## SkillRegistry And MCP-Style Catalog

Phase 6 maps each local tool into `SkillRegistry` metadata with description, input schema, output notes, risk level, and issue types. The MCP-style catalog exposes the same safe local tools through `tools/list` and `tools/call` JSON-RPC style handlers.

This is local discovery and invocation only. It is not a production MCP server and does not call external systems.

## Current Coverage Status

Current available tools are `search_docs`, `read_policy`, `check_user_state`, `check_order_state`, `check_usage_state`, `check_risk_state`, `classify_issue`, `create_ticket`, and `risk_check`.

Current future candidates are `check_payment_state` and `check_invoice_state`.
