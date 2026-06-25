from typing import Any


MOCK_USERS: dict[str, dict[str, Any]] = {
    "user_001": {
        "member_status": "active_member",
        "account_status": "normal_account",
        "eligible_features": [
            "basic_report",
            "advanced_analysis",
            "automation_tasks",
            "batch_export",
            "team_collaboration",
        ],
        "risk_flags": [],
    },
    "user_002": {
        "member_status": "expired_member",
        "account_status": "normal_account",
        "eligible_features": ["basic_report"],
        "risk_flags": ["membership_expired"],
    },
    "user_003": {
        "member_status": "active_member",
        "account_status": "restricted_account",
        "eligible_features": ["basic_report"],
        "risk_flags": ["account_restricted"],
    },
    "user_004": {
        "member_status": "non_member",
        "account_status": "normal_account",
        "eligible_features": ["basic_report"],
        "risk_flags": [],
    },
}


def check_user_state(user_id: str, feature_name: str | None = None) -> dict[str, Any]:
    """Return deterministic local mock user state."""

    state = MOCK_USERS.get(user_id)
    if state is None:
        return {
            "user_id": user_id,
            "member_status": "unknown",
            "account_status": "unknown",
            "eligible_features": [],
            "risk_flags": ["unknown_user"],
            "checked_feature": feature_name,
        }

    return {
        "user_id": user_id,
        "member_status": state["member_status"],
        "account_status": state["account_status"],
        "eligible_features": list(state["eligible_features"]),
        "risk_flags": list(state["risk_flags"]),
        "checked_feature": feature_name,
    }
