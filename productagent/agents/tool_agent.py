import re
from pathlib import Path
from typing import Any, Callable

from productagent.data_loader import PROJECT_ROOT
from productagent.models.base import BaseProvider
from productagent.tool_coverage import split_required_tools
from productagent.tools import (
    check_user_state,
    classify_issue,
    create_ticket,
    read_policy,
    risk_check,
    search_docs,
)
from productagent.tracing import TraceLogger


class ToolAgent:
    """A minimal local tool-using agent with tracing and risk checks."""

    name = "tool"

    def __init__(
        self,
        provider: BaseProvider,
        docs_dir: str | Path | None = None,
        top_k: int = 3,
        trace_logger: TraceLogger | None = None,
    ) -> None:
        self.provider = provider
        self.docs_dir = Path(docs_dir) if docs_dir else PROJECT_ROOT / "data" / "product_docs"
        self.top_k = top_k
        self.trace_logger = trace_logger or TraceLogger()

    def run(
        self,
        task_id: str,
        user_query: str,
        task_type: str,
        expected_answer_points: list[str] | None = None,
        required_tools: list[str] | None = None,
        risk_points: list[str] | None = None,
        user_id: str | None = None,
        tool_availability: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        expected_answer_points = expected_answer_points or []
        required_tools = required_tools or []
        risk_points = risk_points or []
        coverage = split_required_tools(required_tools, tool_availability=tool_availability)
        tool_calls: list[dict[str, Any]] = []
        retrieved_context: list[dict[str, Any]] = []
        trace_id = self.trace_logger.new_trace_id()

        self._log(
            trace_id=trace_id,
            task_id=task_id,
            event_type="task_start",
            payload={"user_query": user_query, "task_type": task_type},
        )

        try:
            classification = self._call_tool(
                trace_id=trace_id,
                task_id=task_id,
                tool_calls=tool_calls,
                tool_name="classify_issue",
                func=classify_issue,
                user_query=user_query,
            )
            issue_type = classification["issue_type"]
            resolved_user_id = user_id or _extract_user_id(user_query) or "unknown"

            if issue_type in {"membership", "account"}:
                self._call_tool(
                    trace_id=trace_id,
                    task_id=task_id,
                    tool_calls=tool_calls,
                    tool_name="check_user_state",
                    func=check_user_state,
                    user_id=resolved_user_id,
                    feature_name=_infer_feature_name(user_query),
                )
                policy_name = "account_policy" if issue_type == "account" else "feature_guide"
                policy_result = self._read_policy_tool(
                    trace_id=trace_id,
                    task_id=task_id,
                    tool_calls=tool_calls,
                    policy_name=policy_name,
                )
                _append_policy_context(retrieved_context, policy_result)

            elif issue_type in {"refund", "payment", "invoice"}:
                policy_name = _policy_for_financial_issue(issue_type)
                policy_result = self._read_policy_tool(
                    trace_id=trace_id,
                    task_id=task_id,
                    tool_calls=tool_calls,
                    policy_name=policy_name,
                )
                _append_policy_context(retrieved_context, policy_result)

            elif issue_type == "product_question":
                docs_result = self._call_tool(
                    trace_id=trace_id,
                    task_id=task_id,
                    tool_calls=tool_calls,
                    tool_name="search_docs",
                    func=search_docs,
                    query=user_query,
                    top_k=self.top_k,
                    docs_dir=self.docs_dir,
                )
                retrieved_context.extend(docs_result)
                self._log(
                    trace_id=trace_id,
                    task_id=task_id,
                    event_type="retrieval",
                    payload={"query": user_query, "result_count": len(docs_result)},
                )

            else:
                ticket_result = self._call_tool(
                    trace_id=trace_id,
                    task_id=task_id,
                    tool_calls=tool_calls,
                    tool_name="create_ticket",
                    func=create_ticket,
                    user_id=resolved_user_id,
                    issue_type=issue_type,
                    summary=user_query[:160],
                )
                if _looks_like_risk_query(user_query):
                    policy_result = self._read_policy_tool(
                        trace_id=trace_id,
                        task_id=task_id,
                        tool_calls=tool_calls,
                        policy_name="risk_rules",
                    )
                    _append_policy_context(retrieved_context, policy_result)
                retrieved_context.append(
                    {
                        "source_file": "mock_ticket",
                        "chunk_id": ticket_result["ticket_id"],
                        "content": f"Created mock ticket {ticket_result['ticket_id']} for {issue_type}.",
                        "score": 1,
                    }
                )

            base_answer = self.provider.generate(
                user_query=user_query,
                task_type=task_type,
                expected_answer_points=expected_answer_points,
                required_tools=[],
                risk_points=risk_points,
                retrieved_context=retrieved_context,
            )
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
                tool_name="risk_check",
                func=risk_check,
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
                "tool_calls": tool_calls,
                "retrieved_context": retrieved_context,
                "final_answer": final_answer,
                "risk_check": risk_result,
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
            tool_availability=task.get("tool_availability"),
        )

    def _read_policy_tool(
        self,
        *,
        trace_id: str,
        task_id: str,
        tool_calls: list[dict[str, Any]],
        policy_name: str,
    ) -> dict[str, Any]:
        return self._call_tool(
            trace_id=trace_id,
            task_id=task_id,
            tool_calls=tool_calls,
            tool_name="read_policy",
            func=read_policy,
            policy_name=policy_name,
            docs_dir=self.docs_dir,
        )

    def _call_tool(
        self,
        *,
        trace_id: str,
        task_id: str,
        tool_calls: list[dict[str, Any]],
        tool_name: str,
        func: Callable[..., Any],
        **kwargs: Any,
    ) -> Any:
        result = func(**kwargs)
        call_record = {
            "tool_name": tool_name,
            "arguments": _safe_arguments(kwargs),
            "result": result,
        }
        tool_calls.append(call_record)
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


def _extract_user_id(user_query: str) -> str | None:
    match = re.search(r"user_\d{3}", user_query)
    if match:
        return match.group(0)
    return None


def _infer_feature_name(user_query: str) -> str | None:
    lowered = user_query.lower()
    if any(token in lowered for token in ["advanced", "premium", "高级", "楂樼骇", "分析", "鍒嗘瀽"]):
        return "advanced_analysis"
    if any(token in lowered for token in ["export", "导出", "瀵煎嚭"]):
        return "batch_export"
    if any(token in lowered for token in ["automation", "自动化", "鑷姩"]):
        return "automation_tasks"
    if any(token in lowered for token in ["team", "团队", "鍥㈤槦"]):
        return "team_collaboration"
    return None


def _policy_for_financial_issue(issue_type: str) -> str:
    if issue_type == "invoice":
        return "faq"
    if issue_type == "payment":
        return "faq"
    return "refund_policy"


def _append_policy_context(retrieved_context: list[dict[str, Any]], policy_result: dict[str, Any]) -> None:
    if not policy_result.get("found"):
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
            lines.append(
                f"- User state for `{user_id}` is unknown in mock data; the answer must ask for further verification."
            )
        else:
            lines.append(
                "- Mock user state: "
                f"member_status={user_state['member_status']}, "
                f"account_status={user_state['account_status']}, "
                f"risk_flags={user_state['risk_flags']}."
            )

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

    lines.append("- Next step: verify policy and user/order state before making any promise.")
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
            "限制",
            "椋庨櫓",
            "缁曡繃",
            "闄愬埗",
        ]
    )
