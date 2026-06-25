# RAG Comparison Report

- Total tasks: 20
- Baseline output: `outputs/baseline_mock_results.jsonl`
- RAG output: `outputs/rag_mock_results.jsonl`

## Retrieved Docs

- account_policy.md
- faq.md
- feature_guide.md
- refund_policy.md
- risk_rules.md

## RAG Improvements Over Baseline

- RAG retrieves product documents before calling the provider.
- RAG results include `retrieved_context` for inspection.
- Product-policy answers are more grounded in local Markdown docs.

## Current Limitations

- Retrieval is keyword-based, not vector search.
- `MockProvider` is deterministic and does not represent a real model.
- This report is kept for backwards compatibility; see `reports/eval_summary.md` for the Phase 3 eval report.
