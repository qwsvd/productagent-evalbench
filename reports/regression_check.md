# Regression Check

- Phase: Phase 6
- Status: ok

| Check | Passed | Details |
| --- | --- | --- |
| file_exists:reports/benchmark_manifest.json | True | "reports/benchmark_manifest.json" |
| file_exists:reports/provider_eval_isolation.md | True | "reports/provider_eval_isolation.md" |
| file_exists:reports/model_benchmark_report.md | True | "reports/model_benchmark_report.md" |
| file_exists:outputs/agent_trace.jsonl | True | "outputs/agent_trace.jsonl" |
| mock_eval_isolation | True | "mock outputs contain provider=mock and provider_mode=mock" |
| tool_strict_accuracy | True | {"hit_count": 38, "total": 38, "accuracy": 1.0} |
| model_benchmark_dry_run_marked | True | "all model benchmark mock records have dry_run=true" |
| env_not_tracked | True | ".env is not tracked by git" |

This check is local-only. It does not run pytest itself and does not call external model providers.
