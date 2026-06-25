import json
from pathlib import Path

from productagent.agents import ToolAgent
from productagent.cli import compare_agents, run_task_set
from productagent.data_loader import PROJECT_ROOT
from productagent.eval.metrics import (
    context_usage_score,
    hallucination_risk,
    task_success_score,
    tool_call_accuracy,
    user_experience_score,
)
from productagent.models import MockProvider
from productagent.tools import (
    check_order_state,
    check_usage_state,
    check_user_state,
    classify_issue,
    read_policy,
    risk_check,
)
from productagent.tracing import TraceLogger


def test_classify_issue_covers_core_types() -> None:
    assert classify_issue("I need a refund")["issue_type"] == "refund"
    assert classify_issue("会员权益怎么查看")["issue_type"] == "membership"
    assert classify_issue("账号登录被限制")["issue_type"] == "account"
    assert classify_issue("How do premium features work?")["issue_type"] == "product_question"


def test_read_policy_reads_product_doc() -> None:
    result = read_policy("refund_policy")

    assert result["found"] is True
    assert result["policy_name"] == "refund_policy"
    assert result["content"]


def test_check_user_state_returns_mock_state() -> None:
    result = check_user_state("user_001", feature_name="advanced_analysis")

    assert result["user_id"] == "user_001"
    assert result["member_status"] == "active_member"
    assert result["account_status"] == "normal_account"
    assert "advanced_analysis" in result["eligible_features"]
    assert result["checked_feature"] == "advanced_analysis"


def test_check_order_state_returns_mock_order_state() -> None:
    result = check_order_state(order_id="order_002")

    assert result["found"] is True
    assert result["order_id"] == "order_002"
    assert result["payment_status"] == "paid"
    assert result["refundable"] is True


def test_check_usage_state_returns_mock_usage_state() -> None:
    result = check_usage_state("user_001", feature_name="advanced_export")

    assert result["found"] is True
    assert result["feature_name"] == "advanced_export"
    assert result["usage_status"] == "available"
    assert result["usage_count"] == 2


def test_risk_check_detects_direct_refund_promise() -> None:
    result = risk_check("We will refund your payment immediately. No review is needed.")

    assert result["risk_level"] == "high"
    assert "direct_refund_promise" in result["risk_points"]


def test_tool_agent_handles_one_task() -> None:
    agent = ToolAgent(provider=MockProvider(), top_k=2)

    result = agent.run(
        task_id="tool_test",
        user_query="user_001 cannot use premium member feature",
        task_type="membership_check",
        expected_answer_points=["check member status"],
        risk_points=["do not fabricate user state"],
        user_id="user_001",
    )

    tool_names = [call["tool_name"] for call in result["tool_calls"]]
    assert result["agent"] == "tool"
    assert result["issue_type"] == "membership"
    assert "classify_issue" in tool_names
    assert "check_user_state" in tool_names
    assert "read_policy" in tool_names
    assert "risk_check" in tool_names
    assert result["risk_check"]["risk_level"] == "low"


def test_tool_agent_returns_unavailable_required_tools() -> None:
    agent = ToolAgent(provider=MockProvider(), top_k=2)

    result = agent.run(
        task_id="tool_future_test",
        user_query="user_001 cannot use batch export because of risk limits",
        task_type="membership_check",
        required_tools=["check_risk_state", "check_user_state"],
        risk_points=[],
        user_id="user_001",
        tool_availability={
            "check_risk_state": "future_mock_unavailable",
            "check_user_state": "available",
        },
    )

    assert result["available_required_tools"] == ["check_user_state"]
    assert result["unavailable_required_tools"] == ["check_risk_state"]
    assert "Current MVP has not implemented" in result["tool_coverage_note"]


def test_tool_agent_feature_question_calls_search_docs() -> None:
    agent = ToolAgent(provider=MockProvider(), top_k=2)

    result = agent.run(
        task_id="tool_feature_test",
        user_query="What is the difference between basic reports and advanced feature guide?",
        task_type="product_qa",
        required_tools=["search_docs"],
        tool_availability={"search_docs": "available"},
    )

    tool_names = [call["tool_name"] for call in result["tool_calls"]]
    assert "search_docs" in tool_names


def test_tool_agent_refund_task_calls_check_order_state() -> None:
    agent = ToolAgent(provider=MockProvider(), top_k=2)

    result = agent.run(
        task_id="tool_refund_test",
        user_query="Can I refund order_002 after payment?",
        task_type="refund_check",
        required_tools=["check_order_state", "read_policy"],
        tool_availability={"check_order_state": "available", "read_policy": "available"},
        order_id="order_002",
    )

    tool_names = [call["tool_name"] for call in result["tool_calls"]]
    assert "read_policy" in tool_names
    assert "check_order_state" in tool_names


def test_tool_agent_membership_usage_task_calls_check_usage_state() -> None:
    agent = ToolAgent(provider=MockProvider(), top_k=2)

    result = agent.run(
        task_id="tool_usage_test",
        user_query="user_001 cannot use advanced export feature",
        task_type="membership_check",
        required_tools=["check_user_state", "check_usage_state"],
        tool_availability={"check_user_state": "available", "check_usage_state": "available"},
        user_id="user_001",
    )

    tool_names = [call["tool_name"] for call in result["tool_calls"]]
    assert "check_user_state" in tool_names
    assert "check_usage_state" in tool_names


def test_trace_logger_writes_jsonl(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    logger = TraceLogger(trace_path)
    trace_id = logger.new_trace_id()

    logger.log(
        trace_id=trace_id,
        task_id="task_001",
        agent="tool",
        provider="mock",
        event_type="tool_call",
        payload={"tool_name": "classify_issue"},
    )

    lines = trace_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["trace_id"] == trace_id
    assert record["event_type"] == "tool_call"


def test_eval_metrics_return_scores() -> None:
    risk_result = {"risk_level": "medium", "risk_points": ["uncertain_without_verification"]}
    answer = "Please check member status. Next, verify the account before making a promise."

    assert task_success_score(answer, ["check member status"]) == 1
    assert hallucination_risk(risk_result) == 0.5
    assert 0 <= user_experience_score(answer, risk_result) <= 1
    assert context_usage_score({"retrieved_context": [{"source_file": "faq.md"}]}) == 1


def test_tool_call_accuracy_scores_only_available_tools() -> None:
    task = {
        "required_tools": ["read_policy", "check_risk_state"],
        "tool_availability": {
            "read_policy": "available",
            "check_risk_state": "future_mock_unavailable",
        },
    }
    result = {"tool_calls": [{"tool_name": "read_policy"}]}

    assert tool_call_accuracy(result, task) == 1.0


def test_tool_call_accuracy_scores_order_and_usage_as_available() -> None:
    task = {
        "required_tools": ["check_order_state", "check_usage_state"],
        "tool_availability": {
            "check_order_state": "available",
            "check_usage_state": "available",
        },
    }
    result = {
        "tool_calls": [
            {"tool_name": "check_order_state"},
            {"tool_name": "check_usage_state"},
        ]
    }

    assert tool_call_accuracy(result, task) == 1.0


def test_future_mock_unavailable_does_not_penalize_accuracy() -> None:
    task = {
        "required_tools": ["check_risk_state"],
        "tool_availability": {"check_risk_state": "future_mock_unavailable"},
    }
    result = {"tool_calls": []}

    assert tool_call_accuracy(result, task) is None


def test_cli_run_tool_writes_results(tmp_path: Path) -> None:
    output_path = tmp_path / "tool_results.jsonl"

    results = run_task_set(
        agent_name="tool",
        provider_name="mock",
        task_set="product_tasks",
        output_path=output_path,
        top_k=2,
    )

    assert len(results) >= 20
    assert output_path.exists()
    assert "tool_calls" in results[0]
    assert "risk_check" in results[0]


def test_cli_compare_three_agents_generates_eval_summary() -> None:
    report_path = compare_agents(
        agent_names=["baseline", "rag", "tool"],
        provider_name="mock",
        task_set="product_tasks",
        project_root=PROJECT_ROOT,
        top_k=2,
    )

    assert report_path == PROJECT_ROOT / "reports" / "eval_summary.md"
    assert report_path.exists()
    assert (PROJECT_ROOT / "reports" / "failure_analysis.md").exists()
    assert (PROJECT_ROOT / "reports" / "tool_trace_report.md").exists()


def test_tool_coverage_doc_exists() -> None:
    assert (PROJECT_ROOT / "docs" / "tool_coverage.md").exists()


def test_product_tasks_jsonl_is_valid_json() -> None:
    path = PROJECT_ROOT / "data" / "tasks" / "product_tasks.jsonl"
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert len(records) >= 20
    assert all("tool_availability" in record for record in records)
