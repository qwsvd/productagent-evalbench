# Evaluation Methodology

## Offline Mock Eval

Mock eval is the stable reproducible benchmark. It uses `MockProvider`, local product docs, local tools, JSONL traces, and heuristic metrics.

## Metrics

- `task_success_score`: keyword/core-term coverage of expected answer points.
- `tool_call_accuracy`: strict match only for required tools marked `available`.
- `hallucination_risk`: derived from local `risk_check`.
- `context_usage_score`: rewards retrieved or tool-provided context.
- `user_experience_score`: rewards clarity, next steps, and safe wording.

## Tool Fairness

`future_mock_unavailable` tools are reported but excluded from strict scoring. This avoids treating future integrations as current routing failures.

## Real Provider Eval

Real-provider eval is stored separately and affected by provider configuration, network, pricing, rate limits, and model version changes. It must not be mixed with mock eval conclusions.

## Evaluator Agent

The evaluator agent is a small offline critic using existing metrics. It provides groundedness, tool-use quality, risk flags, missing context, and suggested fixes.
