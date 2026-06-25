from typing import Any


MOCK_USAGE: dict[tuple[str, str], dict[str, Any]] = {
    ("user_001", "advanced_export"): {
        "usage_status": "available",
        "usage_count": 2,
        "limit": 10,
        "notes": "Advanced export remains available.",
    },
    ("user_002", "advanced_export"): {
        "usage_status": "unavailable",
        "usage_count": 0,
        "limit": 0,
        "notes": "Membership is expired, so advanced features are unavailable.",
    },
    ("user_003", "advanced_export"): {
        "usage_status": "restricted",
        "usage_count": 0,
        "limit": 0,
        "notes": "Account is restricted. Resolve account status before using the feature.",
    },
}


def check_usage_state(user_id: str, feature_name: str | None = None) -> dict[str, Any]:
    """Return deterministic local mock feature usage state."""

    feature = feature_name or "advanced_export"
    usage = MOCK_USAGE.get((user_id, feature))
    if usage is None:
        return {
            "user_id": user_id,
            "found": False,
            "feature_name": feature,
            "usage_status": "unknown",
            "usage_count": 0,
            "limit": 0,
            "notes": "User or feature usage state was not found. Verify before giving a conclusion.",
        }

    return {
        "user_id": user_id,
        "found": True,
        "feature_name": feature,
        "usage_status": usage["usage_status"],
        "usage_count": usage["usage_count"],
        "limit": usage["limit"],
        "notes": usage["notes"],
    }
