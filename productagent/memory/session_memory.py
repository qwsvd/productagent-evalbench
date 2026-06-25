from collections import defaultdict
from datetime import datetime, timezone
from typing import Any


class SessionMemoryStore:
    """In-memory session store for reproducible local experiments."""

    def __init__(self) -> None:
        self._events: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def add_event(self, user_id: str, task_id: str, event_type: str, content: str) -> dict[str, Any]:
        event = {
            "user_id": user_id,
            "task_id": task_id,
            "event_type": event_type,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._events[user_id].append(event)
        return event

    def get_recent_events(self, user_id: str, limit: int = 5) -> list[dict[str, Any]]:
        return list(self._events.get(user_id, []))[-limit:]

    def summarize_user_context(self, user_id: str) -> str:
        events = self.get_recent_events(user_id)
        if not events:
            return ""
        parts = [f"{event['task_id']}:{event['event_type']}={event['content']}" for event in events]
        return " | ".join(parts)

    def clear(self) -> None:
        self._events.clear()
