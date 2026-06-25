import json
from pathlib import Path

from productagent.agents import ToolAgent
from productagent.cli import compare_agents, run_task_set
from productagent.data_loader import PROJECT_ROOT
from productagent.eval.metrics import (
    context_usage_score,
    hallucination_risk,
    task_success_score,
    user_experience_score,
)
from productagent.models import MockProvider
from productagent.tools import check_user_state, classify_issue, read_policy, risk_check
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
    assert "read_feature_guide" in tool_names
    assert "risk_check" in tool_names
    assert result["risk_check"]["risk_level"] == "low"


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
