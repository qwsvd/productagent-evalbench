from typing import Any


SKILLS: list[dict[str, Any]] = [
    {
        "name": "search_docs",
        "description": "Search local product documentation.",
        "input_schema": {"query": "str", "top_k": "int"},
        "output_notes": "Returns source_file, chunk_id, content, and score.",
        "risk_level": "low",
        "when_to_use": "Product or feature questions that need product docs.",
        "underlying_tool": "search_docs",
        "issue_types": ["product_question", "membership", "risk_control"],
    },
    {
        "name": "read_policy",
        "description": "Read one local policy document.",
        "input_schema": {"policy_name": "str"},
        "output_notes": "Returns found/content/error fields.",
        "risk_level": "low",
        "when_to_use": "Policy, refund, account, FAQ, or risk-rule checks.",
        "underlying_tool": "read_policy",
        "issue_types": ["refund", "payment", "invoice", "account", "risk_control", "membership"],
    },
    {
        "name": "check_user_state",
        "description": "Check deterministic mock user membership/account state.",
        "input_schema": {"user_id": "str", "feature_name": "str?"},
        "output_notes": "Local mock state only; not a real user system.",
        "risk_level": "medium",
        "when_to_use": "Membership, account, or permission-sensitive questions.",
        "underlying_tool": "check_user_state",
        "issue_types": ["membership", "account", "product_question"],
    },
    {
        "name": "check_order_state",
        "description": "Check deterministic mock order/payment/refund state.",
        "input_schema": {"order_id": "str?", "user_id": "str?"},
        "output_notes": "Local mock order data only.",
        "risk_level": "medium",
        "when_to_use": "Refund or payment questions involving order state.",
        "underlying_tool": "check_order_state",
        "issue_types": ["refund", "payment", "invoice"],
    },
    {
        "name": "check_usage_state",
        "description": "Check deterministic mock feature usage/quota state.",
        "input_schema": {"user_id": "str", "feature_name": "str?"},
        "output_notes": "Local mock feature usage data only.",
        "risk_level": "medium",
        "when_to_use": "Feature usage, quota, or refund usage checks.",
        "underlying_tool": "check_usage_state",
        "issue_types": ["membership", "refund", "product_question"],
    },
    {
        "name": "check_risk_state",
        "description": "Check deterministic mock risk state and blocked actions.",
        "input_schema": {"user_id": "str?", "account_id": "str?", "order_id": "str?", "issue_type": "str?"},
        "output_notes": "Local mock risk state only; not real risk control.",
        "risk_level": "high",
        "when_to_use": "Refund, account, risk-control, or unknown-state issues.",
        "underlying_tool": "check_risk_state",
        "issue_types": ["refund", "payment", "account", "membership", "risk_control", "unknown"],
    },
    {
        "name": "classify_issue",
        "description": "Classify issue type with deterministic keyword rules.",
        "input_schema": {"user_query": "str"},
        "output_notes": "Returns issue_type, confidence, and matched keywords.",
        "risk_level": "low",
        "when_to_use": "Before routing any task.",
        "underlying_tool": "classify_issue",
        "issue_types": ["all"],
    },
    {
        "name": "create_ticket",
        "description": "Create deterministic mock support ticket.",
        "input_schema": {"user_id": "str", "issue_type": "str", "summary": "str"},
        "output_notes": "Local mock ticket only.",
        "risk_level": "low",
        "when_to_use": "Complaints, unknown issues, or follow-up handoff.",
        "underlying_tool": "create_ticket",
        "issue_types": ["complaint", "unknown"],
    },
    {
        "name": "risk_check",
        "description": "Check answer text for risky promises and unsafe guidance.",
        "input_schema": {"answer_or_plan": "str"},
        "output_notes": "Returns low/medium/high and risk points.",
        "risk_level": "high",
        "when_to_use": "Before final answer for policy or state-sensitive issues.",
        "underlying_tool": "risk_check",
        "issue_types": ["all"],
    },
]


class SkillRegistry:
    def __init__(self, skills: list[dict[str, Any]] | None = None) -> None:
        self._skills = skills or SKILLS

    def list_skills(self) -> list[dict[str, Any]]:
        return [dict(skill) for skill in self._skills]

    def get_skill(self, name: str) -> dict[str, Any] | None:
        for skill in self._skills:
            if skill["name"] == name:
                return dict(skill)
        return None

    def recommend_skills(self, issue_type: str) -> list[dict[str, Any]]:
        recommendations = []
        for skill in self._skills:
            issue_types = skill.get("issue_types", [])
            if "all" in issue_types or issue_type in issue_types:
                recommendations.append(dict(skill))
        return recommendations

    def to_tool_catalog(self) -> list[dict[str, Any]]:
        return [
            {
                "name": skill["name"],
                "description": skill["description"],
                "inputSchema": skill["input_schema"],
            }
            for skill in self._skills
        ]
