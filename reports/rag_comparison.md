# RAG Comparison Report

- 任务总数：20
- Baseline 输出文件：`outputs/baseline_mock_results.jsonl`
- RAG 输出文件：`outputs/rag_mock_results.jsonl`

## RAG 使用了哪些文档

- account_policy.md
- faq.md
- feature_guide.md
- refund_policy.md
- risk_rules.md

## RAG 相比 Baseline 的改进点

- RAG 会先检索产品文档，再把相关片段注入 Provider。
- RAG 结果包含 `retrieved_context`，更方便检查答案参考了哪些文档。
- 对退款、会员权益、账号限制等问题，RAG 能把回答边界收敛到产品政策上下文。

## 当前局限性

- 当前只是关键词检索，不是向量数据库。
- 当前 `MockProvider` 不代表真实模型能力。
- 当前没有 Memory、真实工具调用、Tracing 或自动评分。
- 检索结果只做简单打分，可能遗漏同义表达或复杂语义关系。
