import re
from pathlib import Path
from typing import Any

from productagent.rag.chunker import load_document_chunks


IMPORTANT_KEYWORDS = [
    "退款",
    "退钱",
    "会员",
    "权益",
    "高级",
    "高级功能",
    "高级分析",
    "账号",
    "登录",
    "限制",
    "封禁",
    "验证码",
    "共享",
    "申诉",
    "风险",
    "风控",
    "异常",
    "批量",
    "批量导出",
    "支付",
    "订单",
    "发票",
    "自动化任务",
    "团队协作",
]


class SimpleKeywordRetriever:
    """Simple offline keyword retriever for product Markdown documents."""

    def __init__(self, docs_dir: str | Path, max_chars: int = 500) -> None:
        self.docs_dir = Path(docs_dir)
        self.chunks = load_document_chunks(self.docs_dir, max_chars=max_chars)

    def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        if top_k <= 0:
            return []

        query_terms = _query_terms(query)
        scored: list[dict[str, Any]] = []

        for chunk in self.chunks:
            score = _score_chunk(query_terms, chunk["content"])
            if score <= 0:
                continue
            scored.append(
                {
                    "source_file": chunk["source_file"],
                    "chunk_id": chunk["chunk_id"],
                    "content": chunk["content"],
                    "score": score,
                }
            )

        scored.sort(key=lambda item: (-item["score"], item["source_file"], item["chunk_id"]))
        return scored[:top_k]


def _query_terms(query: str) -> set[str]:
    normalized = query.lower()
    terms = set(re.findall(r"[a-z0-9_]+", normalized))

    for keyword in IMPORTANT_KEYWORDS:
        if keyword in query:
            terms.add(keyword)

    chinese_chars = re.findall(r"[\u4e00-\u9fff]", query)
    for index in range(len(chinese_chars) - 1):
        terms.add("".join(chinese_chars[index : index + 2]))

    return {term for term in terms if len(term) >= 2}


def _score_chunk(query_terms: set[str], content: str) -> int:
    normalized_content = content.lower()
    score = 0
    for term in query_terms:
        if term in normalized_content:
            score += 3 if term in IMPORTANT_KEYWORDS else 1
    return score
