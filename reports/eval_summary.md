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

## ToolAgent Improvements

- Adds deterministic local tool calls before the final answer.
- Records tool calls and risk checks in structured results and traces.
- Uses local policy documents and mock user state instead of free-form guesses.

## Current Limitations

- User state is mock data only.
- Tools are local simulations and do not call real systems.
- Eval metrics are heuristic and are not a substitute for production evaluation.
- No real model provider or real database is connected.
