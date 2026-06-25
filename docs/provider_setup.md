# Provider Setup

## Provider Architecture

Phase 4 adds an OpenAI-compatible provider layer.

`OpenAICompatibleProvider` is the shared stdlib-only HTTP implementation. It builds a chat-completions payload, sends it with `urllib.request`, parses `choices[0].message.content`, and converts configuration or network failures into structured error results.

Implemented providers:

- `MockProvider`: offline deterministic provider used by default tests.
- `DeepSeekProvider`: OpenAI-compatible provider configured by DeepSeek environment variables.
- `QwenProvider`: OpenAI-compatible provider configured by Qwen environment variables.
- `OpenAIProvider`: OpenAI-compatible provider configured by OpenAI environment variables.
- `GeminiProvider`: configurable OpenAI-compatible provider shell for Gemini-compatible endpoints.

## `.env.example`

Copy the template if you want a local reference:

```bash
copy .env.example .env
```

Set environment variables in your shell or local environment manager. The application does not require real keys for mock runs or tests.

## API Key Safety

- Do not commit real API keys.
- Do not paste keys into prompts or chats.
- Do not write keys into README, tests, reports, outputs, or source files.
- `.env`, `*.env`, `.env.local`, and `.env.*.local` are ignored by Git.
- `redact_config()` only reports whether a key is configured or missing.

## Running Mock

```bash
python -m productagent.cli compare --agents baseline,rag,tool --provider mock --task-set product_tasks
```

Mock runs do not need API keys and do not access external networks.

## Trying DeepSeek

Set:

```text
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT_SECONDS=30
```

Then run:

```bash
python -m productagent.cli run --agent tool --provider deepseek --task-set product_tasks
```

Use the latest official DeepSeek console or documentation for `DEEPSEEK_BASE_URL` and `DEEPSEEK_MODEL`.

## Trying Qwen

Set:

```text
QWEN_API_KEY=
QWEN_BASE_URL=
QWEN_MODEL=qwen-plus
QWEN_TIMEOUT_SECONDS=30
```

Then run:

```bash
python -m productagent.cli run --agent tool --provider qwen --task-set product_tasks
```

Use the latest official Qwen console or documentation for `QWEN_BASE_URL` and `QWEN_MODEL`.

## Trying OpenAI

Set:

```text
OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT_SECONDS=30
```

Then run:

```bash
python -m productagent.cli run --agent tool --provider openai --task-set product_tasks
```

OpenAI model names change over time. Set `OPENAI_MODEL` to a currently available model from the official platform.

## Trying Gemini

Set:

```text
GEMINI_API_KEY=
GEMINI_BASE_URL=
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TIMEOUT_SECONDS=30
```

Then run:

```bash
python -m productagent.cli run --agent tool --provider gemini --task-set product_tasks
```

Gemini OpenAI-compatible configuration, base URL, and model names should follow the latest official documentation or console. Phase 4 only provides a configurable provider layer and does not implement complex Gemini-specific adaptation.

## Configuration Check

```bash
python -m productagent.cli providers
```

This command prints only:

- `available`
- `configured`
- `missing_api_key`

It does not print API keys and does not make network calls.

## Provider Eval Isolation

Phase 5 separates mock evaluation from external-provider evaluation.

- `provider_mode=mock`: offline reproducible benchmark using `MockProvider`.
- `provider_mode=external_missing_key`: external provider selected but not configured; result records should show structured setup errors.
- `provider_mode=external_configured`: external provider credentials are present; results should be reviewed separately from mock metrics.

Do not mix mock scores with DeepSeek, Qwen, OpenAI, or Gemini scores in one benchmark conclusion. Real-provider results depend on API keys, network conditions, rate limits, pricing, model versions, and provider response formats.

## Run Metadata

Each CLI run writes result records with:

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

The manifest records the task set, agents, provider, provider mode, output files, report files, schema version, and notes that mock results do not represent real DeepSeek/Qwen/OpenAI/Gemini performance.

## Common Errors

- `provider_not_configured`: missing API key, base URL, or model name.
- `missing_api_key`: provider status command found no API key.
- `provider_request_failed`: HTTP request failed before a valid response was received.
- `provider_response_invalid`: response JSON did not match the expected chat-completions shape.
- `provider_timeout`: provider request timed out.

## Why Tests Do Not Call Real Providers

Default tests must be reproducible, free, and safe. They validate provider configuration, payload construction, CLI recognition, and structured errors without contacting DeepSeek, Qwen, OpenAI, Gemini, or any external network.

## Next Extensions

- Provider cost tracking.
- Latency tracking.
- Retry and backoff.
- Response schema validation.
- Provider comparison reports.
- Separation between real-model evaluation and mock evaluation.
