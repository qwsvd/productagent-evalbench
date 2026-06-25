import json
from pathlib import Path
from typing import Any, Iterable

from productagent.result_schema import attach_result_metadata


def write_jsonl(
    records: Iterable[dict[str, Any]],
    output_path: str | Path,
    run_metadata: dict[str, Any] | None = None,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            output_record = attach_result_metadata(record, run_metadata) if run_metadata else record
            file.write(json.dumps(output_record, ensure_ascii=False) + "\n")
    return path


def write_markdown(content: str, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
