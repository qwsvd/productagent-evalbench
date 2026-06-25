from typing import Any


ISSUE_KEYWORDS: dict[str, list[str]] = {
    "invoice": ["invoice", "receipt", "fa piao", "发票", "開票", "鍙戠エ"],
    "refund": [
        "refund",
        "refunds",
        "money back",
        "退费",
        "退款",
        "退钱",
        "返款",
        "閫€娆",
        "閫€閽",
    ],
    "payment": ["payment", "paid", "pay", "order", "charge", "支付", "订单", "鏀粯", "璁㈠崟"],
    "membership": [
        "membership",
        "member",
        "premium",
        "会员",
        "权益",
        "高级",
        "浼氬憳",
        "鏉冪泭",
        "楂樼骇",
    ],
    "account": [
        "account",
        "login",
        "restricted",
        "unblock",
        "verify code",
        "账号",
        "账户",
        "登录",
        "限制",
        "封禁",
        "验证码",
        "璐﹀彿",
        "鐧诲綍",
        "闄愬埗",
        "灏佺",
        "楠岃瘉",
    ],
    "complaint": ["complaint", "angry", "not satisfied", "投诉", "不满意", "鎶曡瘔", "涓嶆弧鎰"],
    "product_question": [
        "feature",
        "guide",
        "how",
        "what",
        "difference",
        "产品",
        "功能",
        "怎么",
        "什么",
        "区别",
        "浜у搧",
        "鍔熻兘",
        "鎬庝箞",
        "浠€涔",
        "鍖哄埆",
    ],
}


def classify_issue(user_query: str) -> dict[str, Any]:
    """Classify one user query with simple deterministic keyword rules."""

    normalized_query = user_query.lower()
    best_issue_type = "unknown"
    best_matches: list[str] = []

    for issue_type, keywords in ISSUE_KEYWORDS.items():
        matches = [keyword for keyword in keywords if keyword.lower() in normalized_query]
        if len(matches) > len(best_matches):
            best_issue_type = issue_type
            best_matches = matches

    if best_issue_type == "unknown":
        return {
            "issue_type": "unknown",
            "confidence": 0.2,
            "matched_keywords": [],
        }

    confidence = min(0.95, 0.45 + 0.15 * len(best_matches))
    return {
        "issue_type": best_issue_type,
        "confidence": round(confidence, 2),
        "matched_keywords": best_matches,
    }
