from functools import lru_cache
from pathlib import Path
from typing import Any

from productagent.data_loader import PROJECT_ROOT
from productagent.rag.retriever import SimpleKeywordRetriever


def search_docs(
    query: str,
    top_k: int = 3,
    docs_dir: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Search local product Markdown docs with the existing RAG retriever."""

    target_docs_dir = Path(docs_dir) if docs_dir else PROJECT_ROOT / "data" / "product_docs"
    retriever = _get_retriever(str(target_docs_dir.resolve()))
    return retriever.retrieve(query, top_k=top_k)


@lru_cache(maxsize=8)
def _get_retriever(docs_dir: str) -> SimpleKeywordRetriever:
    return SimpleKeywordRetriever(Path(docs_dir))
