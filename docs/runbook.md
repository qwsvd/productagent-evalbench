# ProductAgent-EvalBench Runbook

## Project Goal

ProductAgent-EvalBench is a reproducible local benchmark for product-support agents. It compares BaselineAgent, RagAgent, and ToolAgent with local product tasks, local mock tools, tracing, heuristic eval, and provider abstraction.

## Install

```bash
python -m pip install -e ".[dev]"
```

## Run Tests

```bash
python -m pytest -q
```

## Run Mock Agents

```bash
python -m productagent.cli run --agent baseline --provider mock --task-set product_tasks
python -m productagent.cli run --agent rag --provider mock --task-set product_tasks
python -m productagent.cli run --agent tool --provider mock --task-set product_tasks
```

## Run Mock Compare

```bash
python -m productagent.cli compare --agents baseline,rag,tool --provider mock --task-set product_tasks
```

## Check Outputs

Generated JSONL files live in:

```text
outputs/
```

The core mock outputs are:

```text
outputs/baseline_mock_results.jsonl
outputs/rag_mock_results.jsonl
outputs/tool_mock_results.jsonl
outputs/agent_trace.jsonl
```

Each result record should include `run_id`, `provider_mode`, `schema_version`, `status`, `answer`, `latency_ms`, `estimated_cost_usd`, and `token_usage`.

## Check Reports

Generated reports live in:

```text
reports/
```

Key files:

```text
reports/eval_summary.md
reports/failure_analysis.md
reports/tool_trace_report.md
reports/provider_eval_isolation.md
reports/benchmark_manifest.json
```

## Check Providers

```bash
python -m productagent.cli providers
```

This command does not make network calls. It only reports `available`, `configured`, or `missing_api_key`.

## Configure `.env.example`

Copy the template if you want local provider configuration:

```bash
copy .env.example .env
```

Never commit real API keys. `.env` files are ignored by `.gitignore`.

## Trying External Providers

External providers are configurable but not used in default tests. Prefer validating mock runs first.

Example:

```bash
python -m productagent.cli run --agent tool --provider openai --task-set product_tasks --eval-mode external
```

Use current official provider docs or consoles for base URL and model names. Do not run external providers unless you understand network, cost, rate-limit, and data-handling implications.

## Successful Run Checklist

A run is healthy when:

- The command exits with code 0.
- The expected output JSONL file exists.
- Each result record has `schema_validation.valid=true`.
- `status` is `ok` for mock runs.
- Reports are regenerated when using `compare`.

## Mock vs External Isolation

Mock eval and external eval are separate benchmark modes. Do not combine mock scores with DeepSeek, Qwen, OpenAI, or Gemini scores in one benchmark conclusion.

Check:

- `provider_mode=mock` for mock outputs.
- `provider_mode=external_missing_key` when an external provider lacks a key.
- `provider_mode=external_configured` only when external provider credentials are present.
- `reports/provider_eval_isolation.md` for the isolation rule.

## Common Issues

### GitHub Desktop Shows Clean But Web Page Has Not Refreshed

GitHub Desktop reflects local status. The GitHub web page updates after a commit is pushed and the browser page refreshes.

### `provider_not_configured`

The provider is missing a required API key, base URL, or model setting. This is a provider setup issue, not necessarily an Agent logic failure.

### JSONL Output Location

All result files are under `outputs/`.

### Report Location

All markdown reports and the manifest are under `reports/`.

### Why Tests Do Not Use Real Network Calls

The default test suite must be reproducible, free, and safe. It validates local logic, schema stability, provider configuration status, and mock eval without contacting external model APIs.
