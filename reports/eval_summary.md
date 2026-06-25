# Eval Summary

- Total tasks: 20

## Result Files

- baseline: `outputs/baseline_mock_results.jsonl`
- rag: `outputs/rag_mock_results.jsonl`
- tool: `outputs/tool_mock_results.jsonl`

## Average Metrics

| Agent | Task Success | Hallucination Risk | User Experience |
| --- | ---: | ---: | ---: |
| baseline | 1.000 | 0.000 | 1.000 |
| rag | 1.000 | 0.000 | 1.000 |
| tool | 1.000 | 0.000 | 1.000 |

## Tool Coverage Fairness

- Required tools total: 38
- Available required tools: 38
- Future mock unavailable tools: 0
- Not applicable tools: 0
- Strict `tool_call_accuracy` only scores tools marked `available`.
- `future_mock_unavailable` tools are reasonable future product integrations, so they are reported but excluded from strict scoring.
- Phase 3.6 adds `check_order_state` and `check_usage_state` as local mock business-state tools, so they now count as available tools.
- Phase 3.7 adds `check_risk_state` as a local mock risk-state tool, so risk-state requirements now count as available tools.
- These mock tools do not connect to a real order system, user system, database, or external API.
- `route_reason` explains why ToolAgent selected each tool, improving routing auditability.

## Available Tool Hits

| Agent | Available Hits | Available Total | Strict Tool Accuracy |
| --- | ---: | ---: | ---: |
| baseline | 0 | 38 | 0.000 |
| rag | 0 | 38 | 0.000 |
| tool | 38 | 38 | 1.000 |

## Future Tool Tasks

- No tasks contain future mock unavailable tools.

## ToolAgent Improvements

- Adds deterministic local tool calls before the final answer.
- Records tool calls and risk checks in structured results and traces.
- Uses local policy documents and mock user state instead of free-form guesses.
- Phase 3.6 improves feature-question routing through `search_docs` and adds local mock order/usage checks.
- Phase 3.7 adds mock risk-state checks and `route_reason` for tool-selection explainability.

## Current Limitations

- User state is mock data only.
- Tools are local simulations and do not call real systems.
- Order and usage state are small local mock datasets, not production system integrations.
- Risk state is also local mock data, not a production risk-control system.
- Eval metrics are heuristic and are not a substitute for production evaluation.
- No real model provider or real database is connected.
