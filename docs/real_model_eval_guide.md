# Real Model Eval Guide

This guide is for a first real-provider benchmark. Default project commands do not call external models.

## Step 1: Run Mock First

```bash
python -m productagent.cli model-benchmark --providers mock --agents tool --task-set product_tasks --max-tasks 5 --dry-run
```

Confirm `reports/model_benchmark_report.md`, `reports/model_performance_comparison.md`, and `reports/model_cost_report.md` are generated.

## Step 2: Configure `.env`

Copy:

```bash
copy .env.example .env
```

Set only the provider you want to test. Never commit `.env`.

## Step 3: Start With DeepSeek Or Qwen

These are usually good first candidates for small-cost testing. Use official dashboards for current base URL, model, and pricing.

## Step 4: Run 5 Tasks

```bash
python -m productagent.cli model-benchmark --providers deepseek --agents tool --task-set product_tasks --max-tasks 5 --real-run --budget-usd 1 --max-output-tokens 400 --timeout-seconds 60
```

## Step 5: Check Cost Report

Open:

```text
reports/model_cost_report.md
```

The price table is estimated only. Check official pricing before real runs.

## Step 6: Try Two Lower-Cost Providers

```bash
python -m productagent.cli model-benchmark --providers deepseek,qwen --agents tool --task-set product_tasks --max-tasks 5 --real-run --budget-usd 2 --max-output-tokens 400 --timeout-seconds 60
```

## Step 7: Decide Whether To Try Gemini / OpenAI / Claude

Run only a small sample first. Do not run all models and all tasks at once.

## Step 8: Do Not Commit `.env`

Check:

```bash
git status
git ls-files .env
```

`git ls-files .env` should print nothing.

## Step 9: Stop On Budget Risk

Use `--budget-usd`, `--max-tasks`, and `--max-output-tokens`. The harness returns `budget_exceeded` when estimated budget would be exceeded.

## Step 10: Interpret Results

- `latency_ms`: provider and network latency signal.
- `estimated_cost_usd`: local estimate, not official billing.
- `error_code`: setup/network/provider failure.
- answer quality: review with eval metrics and evaluator report.

Do not mix real-provider results with mock eval summary.
