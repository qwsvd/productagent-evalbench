import re
from pathlib import Path
from typing import Any, Callable

from productagent.data_loader import PROJECT_ROOT
from productagent.memory import SessionMemoryStore
from productagent.models.base import BaseProvider
from productagent.models.provider_response import normalize_provider_response
from productagent.skills import SkillRegistry
from productagent.tool_coverage import split_required_tools
from productagent.tools import (
    check_order_state,
    check_risk_state,
    check_usage_state,
    check_user_state,
    classify_issue,
    create_ticket,
    read_policy,
    risk_check,
    search_docs,
)
from productagent.tracing import TraceLogger


class ToolAgent:
    """A minimal local tool-using agent with tracing and route explanations."""

    name = "tool"

    def __init__(
        self,
        provider: BaseProvider,
        docs_dir: str | Path | None = None,
        top_k: int = 3,
        trace_logger: TraceLogger | None = None,
        memory_mode: str = "off",
        memory_store: SessionMemoryStore | None = None,
        skill_registry: SkillRegistry | None = None,
    ) -> None:
        self.provider = provider
        self.docs_dir = Path(docs_dir) if docs_dir else PROJECT_ROOT / "data" / "product_docs"
        self.top_k = top_k
        self.trace_logger = trace_logger or TraceLogger()
        self.memory_mode = memory_mode
        self.memory_store = memory_store or SessionMemoryStore()
        self.skill_registry = skill_registry or SkillRegistry()

    def run(
        self,
        task_id: str,
        user_query: str,
        task_type: str,
        expected_answer_points: list[str] | None = None,
        required_tools: list[str] | None = None,
        risk_points: list[str] | None = None,
        user_id: str | None = None,
        order_id: str | None = None,
        tool_availability: dict[str, str] | None = None,
        memory_mode: str | None = None,
    ) -> dict[str, Any]:
        expected_answer_points = expected_answer_points or []
        required_tools = required_tools or []
        risk_points = risk_points or []
        coverage = split_required_tools(required_tools, tool_availability=tool_availability)
        tool_calls: list[dict[str, Any]] = []
        selected_tools: list[dict[str, str]] = []
        retrieved_context: list[dict[str, Any]] = []
        trace_id = self.trace_logger.new_trace_id()

        self._log(
            trace_id=trace_id,
            task_id=task_id,
            event_type="task_start",
            payload={"user_query": user_query, "task_type": task_type},
        )

        classification = self._call_tool(
            trace_id=trace_id,
            task_id=task_id,
            tool_calls=tool_calls,
            selected_tools=selected_tools,
            tool_name="classify_issue",
            func=classify_issue,
            reason="classify the user issue before routing",
            user_query=user_query,
        )
        classified_issue_type = classification.get("issue_type", "unknown") if isinstance(classification, dict) else "unknown"
        issue_type = _route_type(user_query, task_type, classified_issue_type)
        resolved_user_id = user_id or _extract_user_id(user_query) or "unknown"
        resolved_order_id = order_id or _extract_order_id(user_query)
        feature_name = _infer_feature_name(user_query)
        active_memory_mode = memory_mode or self.memory_mode
        memory_context = ""
        memory_used = False
        memory_selection_reason = "memory disabled for reproducible default runs"
        if active_memory_mode == "session":
            memory_context = self.memory_store.summarize_user_context(resolved_user_id)
            memory_used = bool(memory_context)
            memory_selection_reason = (
                "session memory enabled and prior context was found"
                if memory_used
                else "session memory enabled but no prior context was found"
            )

        try:
            if _should_search_docs(issue_type, user_query, task_type):
                docs_result = self._call_tool(
                    trace_id=trace_id,
                    task_id=task_id,
                    tool_calls=tool_calls,
                    selected_tools=selected_tools,
                    tool_name="search_docs",
                    func=search_docs,
                    reason="product or feature question requires product documentation lookup",
                    query=user_query,
                    top_k=self.top_k,
                    docs_dir=self.docs_dir,
                )
                if isinstance(docs_result, list):
                    retrieved_context.extend(docs_result)
                    result_count = len(docs_result)
                else:
                    result_count = 0
                self._log(
                    trace_id=trace_id,
                    task_id=task_id,
                    event_type="retrieval",
                    payload={"query": user_query, "result_count": result_count},
                )

            if issue_type == "membership":
                self._call_user_state(trace_id, task_id, tool_calls, selected_tools, resolved_user_id, feature_name)
                policy_result = self._read_policy_tool(
                    trace_id,
                    task_id,
                    tool_calls,
                    selected_tools,
                    "feature_guide",
                    "membership and feature usage issues need the feature guide policy",
                )
                _append_policy_context(retrieved_context, policy_result)
                if _needs_order_check(user_query, task_type, required_tools, resolved_order_id):
                    self._call_order_state(trace_id, task_id, tool_calls, selected_tools, resolved_order_id, resolved_user_id)
                if _needs_usage_check(user_query, task_type, required_tools):
                    self._call_usage_state(trace_id, task_id, tool_calls, selected_tools, resolved_user_id, feature_name)
                self._call_risk_state(trace_id, task_id, tool_calls, selected_tools, resolved_user_id, resolved_order_id, issue_type)

            elif issue_type == "account":
                self._call_user_state(trace_id, task_id, tool_calls, selected_tools, resolved_user_id, feature_name)
                policy_result = self._read_policy_tool(
                    trace_id,
                    task_id,
                    tool_calls,
                    selected_tools,
                    "account_policy",
                    "account issues need account policy before any unblock guidance",
                )
                _append_policy_context(retrieved_context, policy_result)
                self._call_risk_state(trace_id, task_id, tool_calls, selected_tools, resolved_user_id, resolved_order_id, issue_type)

            elif issue_type in {"refund", "payment"}:
                policy_result = self._read_policy_tool(
                    trace_id,
                    task_id,
                    tool_calls,
                    selected_tools,
                    "refund_policy",
                    "refund or payment issues require refund policy lookup before any promise",
                )
                _append_policy_context(retrieved_context, policy_result)
                self._call_order_state(trace_id, task_id, tool_calls, selected_tools, resolved_order_id, resolved_user_id)
                if _needs_usage_check(user_query, task_type, required_tools):
                    self._call_usage_state(trace_id, task_id, tool_calls, selected_tools, resolved_user_id, feature_name)
                self._call_risk_state(trace_id, task_id, tool_calls, selected_tools, resolved_user_id, resolved_order_id, issue_type)

            elif issue_type == "invoice":
                policy_result = self._read_policy_tool(
                    trace_id,
                    task_id,
                    tool_calls,
                    selected_tools,
                    "faq",
                    "invoice issues use FAQ policy and may need order state",
                )
                _append_policy_context(retrieved_context, policy_result)
                if _needs_order_check(user_query, task_type, required_tools, resolved_order_id):
                    self._call_order_state(trace_id, task_id, tool_calls, selected_tools, resolved_order_id, resolved_user_id)
                self._call_risk_state(trace_id, task_id, tool_calls, selected_tools, resolved_user_id, resolved_order_id, issue_type)

            elif issue_type == "product_question":
                if _needs_user_state_check(user_query, required_tools):
                    self._call_user_state(trace_id, task_id, tool_calls, selected_tools, resolved_user_id, feature_name)
                if _needs_usage_check(user_query, task_type, required_tools):
                    self._call_usage_state(trace_id, task_id, tool_calls, selected_tools, resolved_user_id, feature_name)

            elif issue_type == "risk_control":
                policy_result = self._read_policy_tool(
                    trace_id,
                    task_id,
                    tool_calls,
                    selected_tools,
                    "risk_rules",
                    "risk-control issues require local risk rules",
                )
                _append_policy_context(retrieved_context, policy_result)
                self._call_risk_state(trace_id, task_id, tool_calls, selected_tools, resolved_user_id, resolved_order_id, issue_type)

            else:
                self._call_tool(
                    trace_id=trace_id,
                    task_id=task_id,
                    tool_calls=tool_calls,
                    selected_tools=selected_tools,
                    tool_name="create_ticket",
                    func=create_ticket,
                    reason="complaint or unknown issue needs a mock ticket for follow-up",
                    user_id=resolved_user_id,
                    issue_type=issue_type,
                    summary=user_query[:160],
                )
                self._call_risk_state(trace_id, task_id, tool_calls, selected_tools, resolved_user_id, resolved_order_id, issue_type)

            selected_skills = _selected_skills(selected_tools, self.skill_registry)
            route_reason = _build_route_reason(
                issue_type,
                selected_tools,
                selected_skills,
                memory_used,
                memory_selection_reason,
            )
            self._log(
                trace_id=trace_id,
                task_id=task_id,
                event_type="route_decision",
                payload={
                    "issue_type": issue_type,
                    "selected_tools": selected_tools,
                    "selected_skills": selected_skills,
                    "memory_used": memory_used,
                    "summary": _route_summary(issue_type),
                },
            )

            if memory_context:
                retrieved_context.append(
                    {
                        "source_file": "session_memory",
                        "chunk_id": f"{resolved_user_id}#recent",
                        "content": memory_context,
                        "score": 1,
                    }
                )
            provider_output = self.provider.generate(
                user_query=user_query,
                task_type=task_type,
                expected_answer_points=expected_answer_points,
                required_tools=[],
                risk_points=risk_points,
                retrieved_context=retrieved_context,
            )
            base_answer, provider_response = normalize_provider_response(self.provider.name, provider_output)
            final_answer = _compose_tool_answer(
                base_answer=base_answer,
                issue_type=issue_type,
                tool_calls=tool_calls,
                user_id=resolved_user_id,
            )

            risk_result = self._call_tool(
                trace_id=trace_id,
                task_id=task_id,
                tool_calls=tool_calls,
                selected_tools=selected_tools,
                tool_name="risk_check",
                func=risk_check,
                reason="final answer must be checked for risky promises",
                answer_or_plan=final_answer,
            )
            self._log(
                trace_id=trace_id,
                task_id=task_id,
                event_type="risk_check",
                payload={"result": risk_result},
            )
            self._log(
                trace_id=trace_id,
                task_id=task_id,
                event_type="final_answer",
                payload={"final_answer": final_answer},
            )

            result = {
                "task_id": task_id,
                "agent": self.name,
                "provider": self.provider.name,
                "user_query": user_query,
                "issue_type": issue_type,
                "route_reason": route_reason,
                "tool_calls": tool_calls,
                "retrieved_context": retrieved_context,
                "final_answer": final_answer,
                "provider_response": provider_response,
                "risk_check": risk_result,
                "memory_mode": active_memory_mode,
                "memory_used": memory_used,
                "memory_context": memory_context,
                "required_tools": required_tools,
                "available_required_tools": coverage["available"],
                "unavailable_required_tools": coverage["future_mock_unavailable"],
                "not_applicable_required_tools": coverage["not_applicable"],
                "tool_coverage_note": _tool_coverage_note(coverage),
                "expected_answer_points": expected_answer_points,
                "risk_points": risk_points,
            }
            self._log(
                trace_id=trace_id,
                task_id=task_id,
                event_type="task_end",
                payload={"status": "ok", "tool_call_count": len(tool_calls)},
            )
            if active_memory_mode == "session":
                self.memory_store.add_event(
                    user_id=resolved_user_id,
                    task_id=task_id,
                    event_type="task_end",
                    content=f"issue_type={issue_type};risk={risk_result.get('risk_level', 'unknown')}",
                )
            return result

        except Exception as exc:
            self._log(
                trace_id=trace_id,
                task_id=task_id,
                event_type="error",
                payload={"error": str(exc)},
            )
            raise

    def run_task(self, task: dict[str, Any]) -> dict[str, Any]:
        return self.run(
            task_id=task["task_id"],
            user_query=task["user_query"],
            task_type=task["task_type"],
            expected_answer_points=task.get("expected_answer_points", []),
            required_tools=task.get("required_tools", []),
            risk_points=task.get("risk_points", []),
            user_id=task.get("user_id"),
            order_id=task.get("order_id"),
            tool_availability=task.get("tool_availability"),
        )

    def _read_policy_tool(
        self,
        trace_id: str,
        task_id: str,
        tool_calls: list[dict[str, Any]],
        selected_tools: list[dict[str, str]],
        policy_name: str,
        reason: str,
    ) -> dict[str, Any]:
        return self._call_tool(
            trace_id=trace_id,
            task_id=task_id,
            tool_calls=tool_calls,
            selected_tools=selected_tools,
            tool_name="read_policy",
            func=read_policy,
            reason=reason,
            policy_name=policy_name,
            docs_dir=self.docs_dir,
        )

    def _call_user_state(
        self,
        trace_id: str,
        task_id: str,
        tool_calls: list[dict[str, Any]],
        selected_tools: list[dict[str, str]],
        user_id: str,
        feature_name: str | None,
    ) -> dict[str, Any]:
        return self._call_tool(
            trace_id=trace_id,
            task_id=task_id,
            tool_calls=tool_calls,
            selected_tools=selected_tools,
            tool_name="check_user_state",
            func=check_user_state,
            reason="user or membership state is needed before giving account-specific guidance",
            user_id=user_id,
            feature_name=feature_name,
        )

    def _call_order_state(
        self,
        trace_id: str,
        task_id: str,
        tool_calls: list[dict[str, Any]],
        selected_tools: list[dict[str, str]],
        order_id: str | None,
        user_id: str,
    ) -> dict[str, Any]:
        return self._call_tool(
            trace_id=trace_id,
            task_id=task_id,
            tool_calls=tool_calls,
            selected_tools=selected_tools,
            tool_name="check_order_state",
            func=check_order_state,
            reason="refund or payment issue needs mock order and payment state",
            order_id=order_id,
            user_id=user_id if user_id != "unknown" else None,
        )

    def _call_usage_state(
        self,
        trace_id: str,
        task_id: str,
        tool_calls: list[dict[str, Any]],
        selected_tools: list[dict[str, str]],
        user_id: str,
        feature_name: str | None,
    ) -> dict[str, Any]:
        return self._call_tool(
            trace_id=trace_id,
            task_id=task_id,
            tool_calls=tool_calls,
            selected_tools=selected_tools,
            tool_name="check_usage_state",
            func=check_usage_state,
            reason="membership and feature usage issues need mock usage and quota state",
            user_id=user_id,
            feature_name=feature_name or "advanced_export",
        )

    def _call_risk_state(
        self,
        trace_id: str,
        task_id: str,
        tool_calls: list[dict[str, Any]],
        selected_tools: list[dict[str, str]],
        user_id: str,
        order_id: str | None,
        issue_type: str,
    ) -> dict[str, Any]:
        return self._call_tool(
            trace_id=trace_id,
            task_id=task_id,
            tool_calls=tool_calls,
            selected_tools=selected_tools,
            tool_name="check_risk_state",
            func=check_risk_state,
            reason="risk state is needed to avoid unsafe promises or bypass guidance",
            user_id=user_id if user_id != "unknown" else None,
            order_id=order_id,
            issue_type=issue_type,
        )

    def _call_tool(
        self,
        *,
        trace_id: str,
        task_id: str,
        tool_calls: list[dict[str, Any]],
        selected_tools: list[dict[str, str]],
        tool_name: str,
        func: Callable[..., Any],
        reason: str,
        **kwargs: Any,
    ) -> Any:
        try:
            result = func(**kwargs)
        except Exception as exc:
            result = {"found": False, "error": str(exc)}
            self._log(
                trace_id=trace_id,
                task_id=task_id,
                event_type="error",
                payload={"tool_name": tool_name, "error": str(exc)},
            )

        call_record = {
            "tool_name": tool_name,
            "arguments": _safe_arguments(kwargs),
            "result": result,
        }
        tool_calls.append(call_record)
        selected_tools.append({"tool_name": tool_name, "reason": reason})
        self._log(
            trace_id=trace_id,
            task_id=task_id,
            event_type="tool_call",
            payload=call_record,
        )
        return result

    def _log(self, *, trace_id: str, task_id: str, event_type: str, payload: dict[str, Any]) -> None:
        self.trace_logger.log(
            trace_id=trace_id,
            task_id=task_id,
            agent=self.name,
            provider=self.provider.name,
            event_type=event_type,
            payload=payload,
        )


def _build_route_reason(
    issue_type: str,
    selected_tools: list[dict[str, str]],
    selected_skills: list[dict[str, str]],
    memory_used: bool,
    memory_selection_reason: str,
) -> dict[str, Any]:
    return {
        "issue_type": issue_type,
        "selected_tools": selected_tools,
        "selected_skills": selected_skills,
        "skill_selection_reason": "skills are mapped from selected local tools through SkillRegistry",
        "memory_used": memory_used,
        "memory_selection_reason": memory_selection_reason,
        "not_selected_tools": [
            {
                "tool_name": "create_ticket",
                "reason": "not selected when local policy and state tools can handle the issue",
            }
        ]
        if not any(item["tool_name"] == "create_ticket" for item in selected_tools)
        else [],
    }


def _selected_skills(selected_tools: list[dict[str, str]], skill_registry: SkillRegistry) -> list[dict[str, str]]:
    skills: list[dict[str, str]] = []
    seen: set[str] = set()
    for selected_tool in selected_tools:
        tool_name = selected_tool.get("tool_name", "")
        skill = skill_registry.get_skill(tool_name)
        if skill and skill["name"] not in seen:
            skills.append({"name": skill["name"], "risk_level": skill["risk_level"], "when_to_use": skill["when_to_use"]})
            seen.add(skill["name"])
    return skills


def _route_summary(issue_type: str) -> str:
    summaries = {
        "product_question": "Product or feature issue: use docs first.",
        "refund": "Refund issue: check policy, order state, and risk state before risk_check.",
        "payment": "Payment issue: check policy, order state, and risk state before risk_check.",
        "membership": "Membership or usage issue: check user, usage, and risk state.",
        "account": "Account issue: check user state, account policy, and risk state before unblock guidance.",
        "invoice": "Invoice issue: check FAQ policy and relevant order/risk state.",
        "risk_control": "Risk-control issue: check risk rules and risk state.",
    }
    return summaries.get(issue_type, "Unknown or complaint issue: create a ticket and check risk state.")


def _route_type(user_query: str, task_type: str, classified_issue_type: str) -> str:
    if task_type == "risk_control" or _looks_like_risk_query(user_query):
        return "risk_control"
    if task_type == "account_limit" or classified_issue_type == "account":
        return "account"
    if task_type == "refund_check" or classified_issue_type == "refund":
        return "refund"
    if classified_issue_type in {"payment", "invoice"}:
        return classified_issue_type
    if task_type == "membership_check" or classified_issue_type == "membership":
        return "membership"
    if task_type == "product_qa" or _looks_like_feature_query(user_query):
        return "product_question"
    if classified_issue_type == "complaint":
        return "complaint"
    return classified_issue_type


def _extract_user_id(user_query: str) -> str | None:
    match = re.search(r"user_\d{3}", user_query)
    if match:
        return match.group(0)
    return None


def _extract_order_id(user_query: str) -> str | None:
    match = re.search(r"order_\d{3}", user_query)
    if match:
        return match.group(0)
    return None


def _infer_feature_name(user_query: str) -> str | None:
    lowered = user_query.lower()
    if any(token in lowered for token in ["export", "导出", "瀵煎嚭", "批量", "鎵归噺"]):
        return "advanced_export"
    if any(
        token in lowered
        for token in ["advanced", "premium", "feature", "高级", "楂樼骇", "功能", "鍔熻兘", "分析", "鍒嗘瀽"]
    ):
        return "advanced_export"
    if any(token in lowered for token in ["automation", "自动化", "鑷姩"]):
        return "automation_tasks"
    if any(token in lowered for token in ["team", "团队", "鍥㈤槦"]):
        return "team_collaboration"
    return None


def _append_policy_context(retrieved_context: list[dict[str, Any]], policy_result: dict[str, Any]) -> None:
    if not isinstance(policy_result, dict) or not policy_result.get("found"):
        return
    policy_name = policy_result["policy_name"]
    retrieved_context.append(
        {
            "source_file": f"{policy_name}.md",
            "chunk_id": f"{policy_name}#policy",
            "content": policy_result["content"],
            "score": 1,
        }
    )


def _compose_tool_answer(
    *,
    base_answer: str,
    issue_type: str,
    tool_calls: list[dict[str, Any]],
    user_id: str,
) -> str:
    lines = [base_answer, "", "Tool observations:"]
    lines.append(f"- Classified issue type: {issue_type}.")

    user_state = _first_tool_result(tool_calls, "check_user_state")
    if user_state:
        if user_state.get("member_status") == "unknown":
            lines.append(f"- User state for `{user_id}` is unknown in mock data; ask for further verification.")
        else:
            lines.append(
                "- Mock user state: "
                f"member_status={user_state['member_status']}, "
                f"account_status={user_state['account_status']}, "
                f"risk_flags={user_state['risk_flags']}."
            )

    order_state = _first_tool_result(tool_calls, "check_order_state")
    if order_state:
        if order_state.get("found"):
            lines.append(
                "- Mock order state: "
                f"order_id={order_state['order_id']}, "
                f"payment_status={order_state['payment_status']}, "
                f"refundable={order_state['refundable']}."
            )
        else:
            lines.append("- Mock order state was not found; verify order details before concluding.")

    usage_state = _first_tool_result(tool_calls, "check_usage_state")
    if usage_state:
        if usage_state.get("found"):
            lines.append(
                "- Mock usage state: "
                f"feature={usage_state['feature_name']}, "
                f"usage_status={usage_state['usage_status']}, "
                f"usage_count={usage_state['usage_count']}/{usage_state['limit']}."
            )
        else:
            lines.append("- Mock usage state was not found; verify user and feature state before concluding.")

    risk_state = _first_tool_result(tool_calls, "check_risk_state")
    if risk_state:
        if risk_state.get("found"):
            lines.append(
                "- Mock risk state: "
                f"risk_level={risk_state['risk_level']}, "
                f"risk_flags={risk_state['risk_flags']}."
            )
        else:
            lines.append("- Mock risk state was not found; verify before confirming state or making promises.")

    policy_sources = [
        call["tool_name"]
        for call in tool_calls
        if str(call.get("tool_name", "")).startswith("read_") and call.get("result", {}).get("found")
    ]
    if policy_sources:
        lines.append(f"- Local policy documents checked: {', '.join(policy_sources)}.")

    search_result = _first_tool_result(tool_calls, "search_docs")
    if search_result:
        sources = sorted({item.get("source_file", "unknown") for item in search_result})
        lines.append(f"- Search used local product docs: {', '.join(sources)}.")

    ticket_result = _first_tool_result(tool_calls, "create_ticket")
    if ticket_result:
        lines.append(f"- Mock ticket created: {ticket_result['ticket_id']} ({ticket_result['status']}).")

    lines.append("- Next step: verify policy and mock business/risk state before making any promise.")
    return "\n".join(lines)


def _tool_coverage_note(coverage: dict[str, list[str]]) -> str:
    future_tools = coverage["future_mock_unavailable"]
    not_applicable_tools = coverage["not_applicable"]

    notes: list[str] = []
    if future_tools:
        notes.append(
            "Current MVP has not implemented these future tools: "
            + ", ".join(future_tools)
            + ". Local available tools were used for approximate handling."
        )
    if not_applicable_tools:
        notes.append(
            "These required tools are marked not_applicable for strict tool scoring: "
            + ", ".join(not_applicable_tools)
            + "."
        )
    if not notes:
        notes.append("All required tools for strict scoring are available in the MVP tool set.")
    return " ".join(notes)


def _should_search_docs(issue_type: str, user_query: str, task_type: str) -> bool:
    return issue_type == "product_question" or task_type == "product_qa" or _looks_like_feature_query(user_query)


def _needs_order_check(
    user_query: str,
    task_type: str,
    required_tools: list[str],
    order_id: str | None,
) -> bool:
    lowered = user_query.lower()
    return bool(
        order_id
        or "check_order_state" in required_tools
        or task_type in {"refund_check", "payment_check"}
        or any(token in lowered for token in ["order", "paid", "payment", "refund", "订单", "支付", "退款", "璁㈠崟", "鏀粯", "閫€娆"])
    )


def _needs_usage_check(user_query: str, task_type: str, required_tools: list[str]) -> bool:
    lowered = user_query.lower()
    return bool(
        "check_usage_state" in required_tools
        or task_type == "membership_check"
        or any(
            token in lowered
            for token in [
                "usage",
                "limit",
                "quota",
                "feature",
                "advanced",
                "premium",
                "使用",
                "次数",
                "额度",
                "限制",
                "高级",
                "功能",
                "浣跨敤",
                "闄愬埗",
                "楂樼骇",
                "鍔熻兘",
            ]
        )
    )


def _needs_user_state_check(user_query: str, required_tools: list[str]) -> bool:
    lowered = user_query.lower()
    return bool(
        "check_user_state" in required_tools
        or any(token in lowered for token in ["member", "membership", "account", "会员", "账号", "浼氬憳", "璐﹀彿"])
    )


def _looks_like_feature_query(user_query: str) -> bool:
    lowered = user_query.lower()
    return any(
        token in lowered
        for token in [
            "feature",
            "product",
            "guide",
            "use",
            "how",
            "advanced",
            "premium",
            "功能",
            "高级功能",
            "使用",
            "无法使用",
            "怎么用",
            "产品",
            "指南",
            "鍔熻兘",
            "楂樼骇",
            "浣跨敤",
            "浜у搧",
        ]
    )


def _looks_like_risk_query(user_query: str) -> bool:
    lowered = user_query.lower()
    return any(
        token in lowered
        for token in [
            "risk",
            "bypass",
            "avoid detection",
            "绕过",
            "规避",
            "风控",
            "风险",
            "缁曡繃",
            "瑙勯伩",
            "椋庢帶",
            "椋庨櫓",
        ]
    )


def _first_tool_result(tool_calls: list[dict[str, Any]], tool_name: str) -> Any | None:
    for call in tool_calls:
        if call.get("tool_name") == tool_name:
            return call.get("result")
    return None


def _safe_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in arguments.items():
        if isinstance(value, Path):
            safe[key] = str(value)
        else:
            safe[key] = value
    return safe
