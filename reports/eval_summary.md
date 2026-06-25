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
- Available required tools: 31
- Future mock unavailable tools: 7
- Not applicable tools: 0
- Strict `tool_call_accuracy` only scores tools marked `available`.
- `future_mock_unavailable` tools are reasonable future product integrations, so they are reported but excluded from strict scoring.

## Available Tool Hits

| Agent | Available Hits | Available Total | Strict Tool Accuracy |
| --- | ---: | ---: | ---: |
| baseline | 0 | 31 | 0.000 |
| rag | 0 | 31 | 0.000 |
| tool | 30 | 31 | 0.968 |

## Future Tool Tasks

- product_003: check_order_state
- product_005: check_order_state, check_usage_state
- product_006: check_order_state
- product_007: check_order_state
- product_008: check_usage_state
- product_009: check_risk_state

## ToolAgent Improvements

- Adds deterministic local tool calls before the final answer.
- Records tool calls and risk checks in structured results and traces.
- Uses local policy documents and mock user state instead of free-form guesses.

## Current Limitations

- User state is mock data only.
- Tools are local simulations and do not call real systems.
- Eval metrics are heuristic and are not a substitute for production evaluation.
- No real model provider or real database is connected.
