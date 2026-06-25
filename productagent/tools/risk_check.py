from typing import Any


HIGH_RISK_PATTERNS = {
    "direct_refund_promise": [
        "guaranteed refund",
        "refund guaranteed",
        "we will refund",
        "you will get a refund",
        "approved refund",
        "full refund is approved",
        "一定退款",
        "保证退款",
        "直接退款",
        "马上退款",
        "全额退款给你",
    ],
    "direct_unblock_promise": [
        "guaranteed unblock",
        "we will unblock",
        "will lift the restriction",
        "account is now unrestricted",
        "一定解封",
        "直接解封",
        "马上解封",
        "一定解除限制",
    ],
    "fabricated_user_state": [
        "your account is active",
        "your account is normal",
        "your membership is active",
        "your member status is active",
        "你的账号正常",
        "你的会员有效",
        "你一定有该权益",
    ],
    "password_request": [
        "provide your password",
        "send your password",
        "tell me your password",
        "share your password",
        "提供密码",
        "发送密码",
        "告诉我密码",
    ],
}

UNCERTAIN_PATTERNS = ["maybe", "possibly", "probably", "seems", "might", "可能", "大概", "也许", "似乎"]
VERIFY_PATTERNS = [
    "verify",
    "check",
    "confirm",
    "review",
    "audit",
    "核验",
    "检查",
    "确认",
    "审核",
    "further verification",
]


def risk_check(answer_or_plan: str) -> dict[str, Any]:
    """Detect obvious risky promises in an answer or action plan."""

    normalized = answer_or_plan.lower()
    risk_points: list[str] = []

    for risk_name, patterns in HIGH_RISK_PATTERNS.items():
        for pattern in patterns:
            lowered_pattern = pattern.lower()
            if lowered_pattern in normalized and not _is_negated(normalized, lowered_pattern):
                risk_points.append(risk_name)
                break

    has_uncertain_language = any(pattern.lower() in normalized for pattern in UNCERTAIN_PATTERNS)
    has_verification_language = any(pattern.lower() in normalized for pattern in VERIFY_PATTERNS)
    if has_uncertain_language and not has_verification_language:
        risk_points.append("uncertain_without_verification")

    high_risk_names = set(HIGH_RISK_PATTERNS)
    if high_risk_names & set(risk_points):
        risk_level = "high"
        suggestion = "Remove direct promises and route the user through verification or review."
    elif risk_points:
        risk_level = "medium"
        suggestion = "Add a clear verification step before drawing a conclusion."
    else:
        risk_level = "low"
        suggestion = "No obvious high-risk promise detected."

    return {
        "risk_level": risk_level,
        "risk_points": risk_points,
        "suggestion": suggestion,
    }


def _is_negated(text: str, pattern: str) -> bool:
    index = text.find(pattern)
    if index < 0:
        return False
    prefix = text[max(0, index - 24) : index]
    return any(
        marker in prefix
        for marker in [
            "do not",
            "don't",
            "not ",
            "never",
            "avoid",
            "remove",
            "不要",
            "不能",
            "不应",
            "不支持",
            "禁止",
            "避免",
        ]
    )
