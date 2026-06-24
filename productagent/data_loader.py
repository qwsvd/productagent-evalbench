import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc
    return records


def load_task_set(task_set: str, project_root: str | Path | None = None) -> list[dict[str, Any]]:
    root = Path(project_root) if project_root else PROJECT_ROOT
    path = root / "data" / "tasks" / f"{task_set}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"Task set not found: {path}")
    return load_jsonl(path)


def load_product_docs(project_root: str | Path | None = None) -> dict[str, str]:
    root = Path(project_root) if project_root else PROJECT_ROOT
    docs_dir = root / "data" / "product_docs"
    if not docs_dir.exists():
        raise FileNotFoundError(f"Product docs directory not found: {docs_dir}")
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(docs_dir.glob("*.md"))}