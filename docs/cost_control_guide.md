# Cost Control Guide

## Rules

- Do not run all models and all tasks at once.
- Start with 3 to 5 tasks.
- Set `--max-output-tokens` between 300 and 500.
- Keep temperature low; the provider payload uses deterministic settings where possible.
- Avoid unnecessary long context.
- Start with DeepSeek or Qwen.
- Try Gemini, OpenAI, or Claude only on small samples.
- Review `reports/model_cost_report.md` after each run.
- Stop when `budget_exceeded` appears.

## Safe Command

```bash
python -m productagent.cli model-benchmark --providers mock --agents tool --task-set product_tasks --max-tasks 3 --dry-run
```

## Explicit Real Run

```bash
python -m productagent.cli model-benchmark --providers deepseek --agents tool --task-set product_tasks --max-tasks 5 --real-run --budget-usd 1 --max-output-tokens 400 --timeout-seconds 60
```

The local price table is an estimate only. Check official provider pricing before real runs.
