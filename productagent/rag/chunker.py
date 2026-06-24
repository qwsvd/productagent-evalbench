from pathlib import Path
from typing import Any


def chunk_markdown_file(path: str | Path, max_chars: int = 500) -> list[dict[str, Any]]:
    """Split one Markdown file into paragraph-based chunks."""

    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]

    chunks: list[dict[str, Any]] = []
    current_parts: list[str] = []
    current_length = 0

    for paragraph in paragraphs:
        paragraph_length = len(paragraph)
        if current_parts and current_length + paragraph_length > max_chars:
            chunks.append(_build_chunk(file_path.name, len(chunks), current_parts))
            current_parts = []
            current_length = 0
        current_parts.append(paragraph)
        current_length += paragraph_length

    if current_parts:
        chunks.append(_build_chunk(file_path.name, len(chunks), current_parts))

    return chunks


def load_document_chunks(docs_dir: str | Path, max_chars: int = 500) -> list[dict[str, Any]]:
    """Load and chunk every Markdown document in a directory."""

    directory = Path(docs_dir)
    if not directory.exists():
        raise FileNotFoundError(f"Product docs directory not found: {directory}")

    chunks: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.md")):
        chunks.extend(chunk_markdown_file(path, max_chars=max_chars))
    return chunks


def _build_chunk(source_file: str, index: int, parts: list[str]) -> dict[str, Any]:
    return {
        "source_file": source_file,
        "chunk_id": f"{source_file}#chunk-{index + 1:03d}",
        "content": "\n\n".join(parts),
    }
