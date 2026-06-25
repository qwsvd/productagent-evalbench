import hashlib
from typing import Any


def create_ticket(user_id: str, issue_type: str, summary: str) -> dict[str, Any]:
    """Create a deterministic mock ticket record."""

    raw_key = f"{user_id}|{issue_type}|{summary}".encode("utf-8")
    ticket_id = "mock_ticket_" + hashlib.sha1(raw_key).hexdigest()[:10]
    return {
        "ticket_id": ticket_id,
        "user_id": user_id,
        "issue_type": issue_type,
        "summary": summary,
        "status": "created",
    }
