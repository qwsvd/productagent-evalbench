import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from productagent.data_loader import PROJECT_ROOT


class TraceLogger:
    """Small JSONL trace writer. Logging failures never break agent runs."""

    def __init__(self, output_path: str | Path | None = None, run_metadata: dict[str, Any] | None = None) -> None:
        self.output_path = Path(output_path) if output_path else PROJECT_ROOT / "outputs" / "agent_trace.jsonl"
        self.run_metadata = run_metadata or {}

    def new_trace_id(self) -> str:
        return str(uuid.uuid4())

    def clear(self) -> None:
        try:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            self.output_path.write_text("", encoding="utf-8")
        except OSError:
            return

    def set_run_metadata(self, run_metadata: dict[str, Any] | None) -> None:
        self.run_metadata = run_metadata or {}

    def log(
        self,
        *,
        trace_id: str,
        task_id: str,
        agent: str,
        provider: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        try:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            record = {
                "trace_id": trace_id,
                "task_id": task_id,
                "agent": agent,
                "provider": provider,
                "run_id": self.run_metadata.get("run_id"),
                "provider_mode": self.run_metadata.get("provider_mode"),
                "schema_version": self.run_metadata.get("schema_version"),
                "event_type": event_type,
                "payload": payload,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            with self.output_path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            return
