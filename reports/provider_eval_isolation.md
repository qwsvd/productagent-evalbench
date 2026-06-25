# Provider Evaluation Isolation

- Current provider: `mock`
- Current provider mode: `mock`

## Mock Eval

Mock eval is the offline reproducible benchmark. It uses `MockProvider`, local product docs, local tools, local tracing, and heuristic metrics. It is designed to be rerun without API keys, network access, model cost, or provider availability risk.

## External Provider Eval

External provider eval can use DeepSeek, Qwen, OpenAI, or Gemini through the OpenAI-compatible provider layer, but those runs depend on user-provided API keys, current provider base URLs, model versions, network conditions, rate limits, and cost.

## Isolation Rule

Do not mix mock scores with real-provider scores in the same benchmark conclusion. DeepSeek, Qwen, OpenAI, and Gemini performance must be run separately, stored separately, and reported with provider metadata.

## No Fabricated Benchmark

This project does not fabricate DeepSeek, Qwen, OpenAI, or Gemini quality metrics. If a provider is not configured, results should show structured provider errors such as `provider_not_configured` rather than pretend model answers.

## Future Comparison Fields

Future real-provider reports can add latency, cost, token usage, error-rate comparison, retry counts, and provider-specific response validation.
