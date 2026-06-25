# Provider Setup

## Provider Architecture

The project supports one offline provider and five configurable external providers:

- `MockProvider`: deterministic offline provider used by default tests.
- `DeepSeekProvider`: OpenAI-compatible provider configured through DeepSeek environment variables.
- `QwenProvider`: OpenAI-compatible provider configured through Qwen environment variables.
- `OpenAIProvider`: OpenAI-compatible provider configured through OpenAI environment variables.
- `GeminiProvider`: configurable OpenAI-compatible provider shell for Gemini-compatible endpoints.
- `ClaudeProvider`: configurable provider shell for Claude-compatible endpoints.

`OpenAICompatibleProvider` is the shared stdlib-only HTTP implementation for compatible chat-completions style APIs. It uses `urllib.request`, returns structured provider errors, and never prints API keys.

## `.env.example`

Copy the template only for local use:

```bash
copy .env.example .env
```

Do not commit `.env`. The application does not require real keys for mock runs, tests, CI, smoke tests, experiments, or dry-run model benchmarks.

## API Key Safety

- Do not commit real API keys.
- Do not paste keys into prompts or chats.
- Do not write keys into README, tests, reports, outputs, or source files.
- `.env`, `*.env`, `.env.local`, and `.env.*.local` are ignored by Git.
- `redact_config()` only reports whether a key is configured or missing.

## Configuration Check

```bash
python -m productagent.cli providers
```

This command prints only `available`, `configured`, or `missing_api_key`. It does not make network calls.

## Mock Run

```bash
python -m productagent.cli compare --agents baseline,rag,tool --provider mock --task-set product_tasks
```

Mock runs do not need API keys and do not access external networks.

## External Provider Run

Single-provider run:

```bash
python -m productagent.cli run --agent tool --provider deepseek --task-set product_tasks
```

Real benchmark run is more guarded:

```bash
python -m productagent.cli model-benchmark --providers deepseek --agents tool --task-set product_tasks --max-tasks 5 --real-run --budget-usd 1 --max-output-tokens 400 --timeout-seconds 60
```

Use the latest official provider console or documentation for base URLs, model names, pricing, and API compatibility.

## Provider Eval Isolation

- `provider_mode=mock`: offline reproducible benchmark using `MockProvider`.
- `provider_mode=external_missing_key`: external provider selected but not configured.
- `provider_mode=external_configured`: external provider credentials are present.

Do not mix mock scores with DeepSeek, Qwen, OpenAI, Gemini, or Claude scores in one benchmark conclusion. Real-provider results depend on API keys, network conditions, rate limits, pricing, model versions, and provider response formats.

## Run Metadata

Each CLI result record includes:

- `run_id`
- `timestamp`
- `agent`
- `provider`
- `provider_mode`
- `eval_mode`
- `task_set`
- `project_phase`
- `schema_version`

These fields are generated locally and never include API keys.

## Benchmark Manifest

Mock compare runs generate:

```text
reports/benchmark_manifest.json
```

The manifest records task set, agents, provider, provider mode, outputs, reports, schema version, and notes that mock results do not represent real-provider performance.

## Common Errors

- `provider_not_configured`: missing API key, base URL, or model name.
- `missing_api_key`: provider status command found no API key.
- `dry_run_external_skipped`: external provider was selected, but `--real-run` was not set.
- `budget_exceeded`: projected or accumulated estimated cost exceeded the configured budget.
- `provider_request_failed`: HTTP request failed before a valid response was received.
- `provider_response_invalid`: response JSON did not match the expected chat-completions shape.
- `provider_timeout`: provider request timed out.

## Why Tests Do Not Call Real Providers

Default tests must be reproducible, free, and safe. They validate provider configuration, provider status, structured errors, CLI recognition, and dry-run behavior without contacting DeepSeek, Qwen, OpenAI, Gemini, Claude, or any external network.

## Next Extensions

- Provider-specific request adapters.
- Retry and backoff.
- Response schema validation.
- Cost tracking with official pricing snapshots.
- Latency percentile tracking.
- Real-provider comparison reports stored separately from mock eval.
