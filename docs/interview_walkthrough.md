# Interview Walkthrough

## 30-Second Summary

ProductAgent-EvalBench is a local and optional-real-provider benchmark for product-support agents. It compares baseline prompting, RAG, and tool-using agents with tracing, eval metrics, tool fairness, memory, skills, MCP-style tools, provider abstraction, and cost-aware model benchmarking.

## Demo Path

```bash
python -m pytest -q
python -m productagent.cli providers
python -m productagent.cli compare --agents baseline,rag,tool --provider mock --task-set product_tasks
python -m productagent.cli experiments
python -m productagent.cli model-benchmark --providers mock --agents tool --task-set product_tasks --max-tasks 3 --dry-run
python -m productagent.cli regression-check
```

## What To Emphasize

- Mock eval is reproducible.
- Real-provider eval is opt-in and cost guarded.
- Tool accuracy is scored fairly with availability metadata.
- Route reasons and traces make tool selection debuggable.
- Reports separate agent logic failures from provider setup failures.
