# ProductAgent-EvalBench Runbook

## Project Goal

ProductAgent-EvalBench is a local and optional-real-provider benchmark for product-support agents. It compares BaselineAgent, RagAgent, ToolAgent, ToolAgent with session memory, and optional external providers while keeping mock eval and real-provider eval isolated.

## Install

```bash
python -m pip install -e ".[dev]"
```

## Run Tests

```bash
python -m pytest -q
```

## Inspect Providers

```bash
python -m productagent.cli providers
```

This does not make network calls.

## Inspect Skills

```bash
python -m productagent.cli skills
```

## Inspect MCP-Style Tools

```bash
python -m productagent.cli mcp-tools
```

This lists local safe tools only. It does not start a service and does not call external APIs.

## Run Mock Agents

```bash
python -m productagent.cli run --agent baseline --provider mock --task-set product_tasks
python -m productagent.cli run --agent rag --provider mock --task-set product_tasks
python -m productagent.cli run --agent tool --provider mock --task-set product_tasks
python -m productagent.cli run --agent tool --provider mock --task-set product_tasks --memory-mode session
```

## Run Mock Compare

```bash
python -m productagent.cli compare --agents baseline,rag,tool --provider mock --task-set product_tasks
```

## Run Experiments

```bash
python -m productagent.cli experiments
```

This writes:

```text
reports/experiment_matrix.json
reports/optimization_report.md
reports/ablation_report.md
reports/context_engineering_report.md
reports/evaluator_agent_report.md
```

## Run Model Benchmark Dry Run

```bash
python -m productagent.cli model-benchmark --providers mock --agents tool --task-set product_tasks --max-tasks 3 --dry-run
```

Dry-run mode is the default safe mode. It does not call external models.

## Run Regression Check

```bash
python -m productagent.cli regression-check
```

## Run Smoke Test

```bash
python scripts/smoke_test.py
```

The smoke test runs local CLI commands and checks expected outputs/reports.

## Outputs

Generated JSONL files live in:

```text
outputs/
```

Core files:

```text
outputs/baseline_mock_results.jsonl
outputs/rag_mock_results.jsonl
outputs/tool_mock_results.jsonl
outputs/agent_trace.jsonl
outputs/model_benchmark_mock.jsonl
```

## Reports

Generated reports live in:

```text
reports/
```

Important reports:

```text
reports/eval_summary.md
reports/failure_analysis.md
reports/tool_trace_report.md
reports/provider_eval_isolation.md
reports/benchmark_manifest.json
reports/model_benchmark_report.md
reports/model_performance_comparison.md
reports/model_cost_report.md
reports/regression_check.md
```

## Configure `.env.example`

```bash
copy .env.example .env
```

Do not commit `.env`. Mock runs do not require `.env`.

## Trying External Providers

Prefer mock first. Only run external providers when you understand API keys, network, cost, rate limits, and model-version risk.

```bash
python -m productagent.cli model-benchmark --providers deepseek --agents tool --task-set product_tasks --max-tasks 5 --real-run --budget-usd 1 --max-output-tokens 400 --timeout-seconds 60
```

## Successful Run Checklist

- The command exits with code 0.
- The expected output file exists.
- Mock result records have `provider_mode=mock`.
- External missing-key records have `provider_mode=external_missing_key`.
- Reports clearly state whether results are mock or external.
- No API key appears in outputs or reports.

## Mock vs External Isolation

Mock eval is the offline reproducible benchmark. External eval is affected by API keys, network, rate limits, model versions, and cost. Do not combine mock scores with DeepSeek, Qwen, OpenAI, Gemini, or Claude scores in one conclusion.

## Common Issues

### GitHub Desktop Shows Clean But Web Page Has Not Refreshed

GitHub Desktop reflects local status. GitHub web updates after a commit is pushed and the browser refreshes.

### `provider_not_configured`

The provider is missing a required API key, base URL, or model setting.

### JSONL Output Location

All result files are under `outputs/`.

### Reports Location

Markdown reports and manifests are under `reports/`.

### Why Tests Do Not Use Real Network Calls

The default suite must be reproducible, free, and safe. It validates local logic, schemas, provider status, and dry-run behavior without external model APIs.
