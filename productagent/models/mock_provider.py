from typing import Sequence

from productagent.models.base import BaseProvider


class MockProvider(BaseProvider):
    """Offline provider that returns deterministic simulated answers."""

    name = "mock"

    TASK_TYPE_LABELS = {
        "product_qa": "产品知识问答",
        "policy_check": "规则核对",
        "refund_check": "退款规则判断",
        "membership_check": "会员权益判断",
        "account_limit": "账号限制判断",
        "issue_classification": "问题分类",
        "risk_control": "风险控制",
    }

    def generate(
        self,
        user_query: str,
        task_type: str,
        expected_answer_points: Sequence[str] | None = None,
        required_tools: Sequence[str] | None = None,
        risk_points: Sequence[str] | None = None,
    ) -> str:
        expected_answer_points = list(expected_answer_points or [])
        required_tools = list(required_tools or [])
        risk_points = list(risk_points or [])

        task_label = self.TASK_TYPE_LABELS.get(task_type, task_type)
        intent = self._infer_intent(user_query, task_type)
        answer = [
            f"模拟答复：已按“{task_label}”处理该问题。",
            f"问题判断：{intent}。",
            "建议回复：请先核对产品文档与用户状态，再给出受规则约束的说明。",
        ]

        if expected_answer_points:
            answer.append("应覆盖要点：" + "；".join(expected_answer_points) + "。")

        if required_tools:
            answer.append("模拟需要工具：" + "、".join(required_tools) + "。MVP 阶段不实际调用工具。")

        if risk_points:
            answer.append("风险提醒：" + "；".join(risk_points) + "。")

        return "\n".join(answer)

    def _infer_intent(self, user_query: str, task_type: str) -> str:
        if task_type == "issue_classification":
            return self._classify_issue(user_query)
        if "退款" in user_query or "退钱" in user_query:
            return "需要核对订单、使用情况和退款政策"
        if "会员" in user_query or "高级" in user_query or "权益" in user_query:
            return "需要核对会员状态、权益范围和功能开通条件"
        if "账号" in user_query or "登录" in user_query or "封禁" in user_query or "限制" in user_query:
            return "需要核对账号状态、限制原因和申诉路径"
        if "风险" in user_query or "风控" in user_query or "异常" in user_query:
            return "需要识别风险场景，避免承诺绕过规则"
        return "需要基于产品文档给出简明说明"

    def _classify_issue(self, user_query: str) -> str:
        if "退款" in user_query or "发票" in user_query:
            return "分类为订单与退款问题"
        if "会员" in user_query or "权益" in user_query:
            return "分类为会员权益问题"
        if "登录" in user_query or "账号" in user_query:
            return "分类为账号问题"
        if "风控" in user_query or "异常" in user_query:
            return "分类为风险控制问题"
        return "分类为产品使用咨询"