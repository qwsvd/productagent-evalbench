from typing import Any


MOCK_RISK_STATES: dict[str, dict[str, Any]] = {
    "user_001": {
        "risk_level": "low",
        "risk_flags": [],
        "allowed_actions": ["answer_policy", "suggest_next_step", "create_ticket"],
        "blocked_actions": ["promise_refund", "promise_unblock"],
        "notes": "Normal user, but the agent still must not directly promise refunds or unblocks.",
    },
    "user_002": {
        "risk_level": "medium",
        "risk_flags": ["expired_member", "payment_review_needed"],
        "allowed_actions": ["answer_policy", "check_order_state", "create_ticket"],
        "blocked_actions": ["promise_refund", "promise_membership_restore"],
        "notes": "Membership is expired or payment state needs verification.",
    },
    "user_003": {
        "risk_level": "high",
        "risk_flags": ["restricted_account", "abuse_or_security_review"],
        "allowed_actions": ["answer_policy", "create_ticket", "suggest_account_review"],
        "blocked_actions": ["promise_unblock", "promise_refund", "bypass_risk_control"],
        "notes": "Account is restricted and requires manual or security review.",
    },
}


def check_risk_state(
    user_id: str | None = None,
    account_id: str | None = None,
    order_id: str | None = None,
    issue_type: str | None = None,
) -> dict[str, Any]:
    """Return deterministic local mock risk state."""

    lookup_user_id = user_id or account_id
    risk_state = MOCK_RISK_STATES.get(lookup_user_id or "")
    if risk_state is None:
        return {
            "found": False,
            "user_id": user_id,
            "account_id": account_id,
            "order_id": order_id,
            "issue_type": issue_type,
            "risk_level": "unknown",
            "risk_flags": ["unknown_user_or_state"],
            "allowed_actions": ["answer_general_policy", "create_ticket"],
            "blocked_actions": ["promise_refund", "promise_unblock", "confirm_user_state"],
            "notes": "Risk state was not found. Verify before confirming user, order, refund, or unblock status.",
        }

    return {
        "found": True,
        "user_id": lookup_user_id,
        "account_id": account_id,
        "order_id": order_id,
        "issue_type": issue_type,
        "risk_level": risk_state["risk_level"],
        "risk_flags": list(risk_state["risk_flags"]),
        "allowed_actions": list(risk_state["allowed_actions"]),
        "blocked_actions": list(risk_state["blocked_actions"]),
        "notes": risk_state["notes"],
    }
