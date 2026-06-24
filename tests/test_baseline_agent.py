from pathlib import Path

from productagent.agents import BaselineAgent
from productagent.cli import run_task_set
from productagent.models import MockProvider


def test_baseline_agent_handles_one_task() -> None:
    agent = BaselineAgent(provider=MockProvider())

    result = agent.run(
        task_id="product_test",
        user_query="我开通会员后为什么不能用高级功能？",
        task_type="membership_check",
        expected_answer_points=["需要检查会员状态"],
        required_tools=["check_user_state"],
        risk_points=["不要编造用户会员状态"],
    )

    assert result["task_id"] == "product_test"
    assert result["agent"] == "baseline"
    assert result["provider"] == "mock"
    assert isinstance(result["final_answer"], str)
    assert result["expected_answer_points"] == ["需要检查会员状态"]
    assert result["risk_points"] == ["不要编造用户会员状态"]


def test_cli_run_baseline_writes_results(tmp_path: Path) -> None:
    output_path = tmp_path / "baseline_results.jsonl"

    results = run_task_set(
        agent_name="baseline",
        provider_name="mock",
        task_set="product_tasks",
        output_path=output_path,
    )

    assert len(results) >= 20
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").strip()
