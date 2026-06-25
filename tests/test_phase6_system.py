import json
from pathlib import Path

from productagent.agents import EvaluatorAgent, ToolAgent
from productagent.benchmarks.benchmark_config import BenchmarkConfig
from productagent.benchmarks.cost_tracker import BudgetTracker
from productagent.benchmarks.model_benchmark import run_model_benchmark
from productagent.benchmarks.performance_tracker import summarize_performance
from productagent.cli import compare_agents, main, provider_config_statuses
from productagent.data_loader import PROJECT_ROOT
from productagent.eval.regression_check import run_regression_check
from productagent.mcp import handle_jsonrpc_request
from productagent.memory import SessionMemoryStore
from productagent.models import ClaudeProvider, MockProvider
from productagent.skills import SkillRegistry


def test_claude_provider_missing_key_does_not_crash(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("CLAUDE_BASE_URL", raising=False)
    provider = ClaudeProvider()

    result = provider.generate(user_query="hello", task_type="product_qa")

    assert result["status"] == "error"
    assert result["error_code"] == "provider_not_configured"


def test_providers_command_contains_claude(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    statuses = provider_config_statuses()

    assert "claude" in statuses
    assert statuses["claude"] == "missing_api_key"


def test_session_memory_store_add_retrieve_clear() -> None:
    store = SessionMemoryStore()
    store.add_event("user_001", "task_001", "task_end", "checked membership")

    assert len(store.get_recent_events("user_001")) == 1
    assert "checked membership" in store.summarize_user_context("user_001")

    store.clear()
    assert store.get_recent_events("user_001") == []


def test_tool_agent_default_memory_mode_off() -> None:
    agent = ToolAgent(provider=MockProvider())

    result = agent.run(
        task_id="memory_off",
        user_query="How do advanced features work?",
        task_type="product_qa",
    )

    assert result["memory_mode"] == "off"
    assert result["memory_used"] is False


def test_tool_agent_session_memory_outputs_context() -> None:
    store = SessionMemoryStore()
    store.add_event("user_001", "old_task", "task_end", "previous advanced_export issue")
    agent = ToolAgent(provider=MockProvider(), memory_mode="session", memory_store=store)

    result = agent.run(
        task_id="memory_session",
        user_query="user_001 cannot use advanced export",
        task_type="membership_check",
        user_id="user_001",
    )

    assert result["memory_mode"] == "session"
    assert result["memory_used"] is True
    assert "previous advanced_export issue" in result["memory_context"]
    assert result["route_reason"]["memory_used"] is True


def test_skill_registry_list_and_recommend() -> None:
    registry = SkillRegistry()

    names = [skill["name"] for skill in registry.list_skills()]

    assert "search_docs" in names
    assert any(skill["name"] == "read_policy" for skill in registry.recommend_skills("refund"))


def test_mcp_tools_list_and_call() -> None:
    listed = handle_jsonrpc_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    called = handle_jsonrpc_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "classify_issue", "arguments": {"user_query": "refund request"}},
        }
    )

    assert listed["result"]["tools"]
    assert called["result"]["content"]["issue_type"] == "refund"


def test_mcp_unknown_tool_error() -> None:
    result = handle_jsonrpc_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "unknown_tool", "arguments": {}},
        }
    )

    assert result["error"]["code"] == "tool_not_found"


def test_cli_skills_and_mcp_tools(capsys) -> None:
    assert main(["skills"]) == 0
    skills_output = capsys.readouterr().out
    assert "search_docs" in skills_output

    assert main(["mcp-tools"]) == 0
    tools_output = capsys.readouterr().out
    assert "tools" in tools_output


def test_cli_experiments_generates_reports() -> None:
    assert main(["experiments"]) == 0

    assert (PROJECT_ROOT / "reports" / "experiment_matrix.json").exists()
    assert (PROJECT_ROOT / "reports" / "optimization_report.md").exists()
    assert (PROJECT_ROOT / "reports" / "ablation_report.md").exists()
    assert (PROJECT_ROOT / "reports" / "context_engineering_report.md").exists()
    assert (PROJECT_ROOT / "reports" / "evaluator_agent_report.md").exists()


def test_model_benchmark_dry_run_mock_no_network() -> None:
    records = run_model_benchmark(
        BenchmarkConfig(
            providers=["mock"],
            agents=["tool"],
            task_set="product_tasks",
            max_tasks=1,
            dry_run=True,
            real_run=False,
        ),
        project_root=PROJECT_ROOT,
    )

    assert records[0]["provider"] == "mock"
    assert records[0]["dry_run"] is True
    assert (PROJECT_ROOT / "reports" / "model_benchmark_report.md").exists()


def test_model_benchmark_external_without_real_run_skips(monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-not-used")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://example.invalid/v1")

    records = run_model_benchmark(
        BenchmarkConfig(
            providers=["deepseek"],
            agents=["tool"],
            task_set="product_tasks",
            max_tasks=1,
            dry_run=True,
            real_run=False,
        ),
        project_root=PROJECT_ROOT,
    )

    assert records[0]["error_code"] == "dry_run_external_skipped"


def test_model_benchmark_real_run_missing_key_returns_error(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    records = run_model_benchmark(
        BenchmarkConfig(
            providers=["deepseek"],
            agents=["tool"],
            task_set="product_tasks",
            max_tasks=1,
            dry_run=False,
            real_run=True,
            budget_usd=1,
            max_output_tokens=400,
        ),
        project_root=PROJECT_ROOT,
    )

    assert records[0]["error_code"] == "provider_not_configured"


def test_cost_tracker_budget_exceeded() -> None:
    tracker = BudgetTracker(budget_usd=0.01)

    assert tracker.can_spend(0.02) is False
    assert tracker.budget_exceeded_result()["error_code"] == "budget_exceeded"


def test_performance_tracker_aggregates_latency_error_cost() -> None:
    rows = summarize_performance(
        [
            {"provider": "mock", "agent": "tool", "status": "ok", "latency_ms": 10, "estimated_cost_usd": 0.0},
            {
                "provider": "mock",
                "agent": "tool",
                "status": "error",
                "error_code": "provider_timeout",
                "latency_ms": 30,
                "estimated_cost_usd": 0.0,
            },
        ]
    )

    assert rows[0]["tasks_run"] == 2
    assert rows[0]["success_count"] == 1
    assert rows[0]["timeout_count"] == 1
    assert rows[0]["avg_latency_ms"] == 20


def test_evaluator_agent_outputs_feedback() -> None:
    feedback = EvaluatorAgent().evaluate(
        {"task_id": "task_001", "expected_answer_points": ["refund policy"], "required_tools": []},
        {"task_id": "task_001", "final_answer": "refund policy", "tool_calls": [], "retrieved_context": []},
    )

    assert "groundedness" in feedback
    assert "suggested_fix" in feedback


def test_regression_check_generates_report() -> None:
    compare_agents(
        agent_names=["baseline", "rag", "tool"],
        provider_name="mock",
        task_set="product_tasks",
        project_root=PROJECT_ROOT,
        top_k=1,
    )
    run_model_benchmark(
        BenchmarkConfig(providers=["mock"], agents=["tool"], task_set="product_tasks", max_tasks=1),
        project_root=PROJECT_ROOT,
    )

    result = run_regression_check(PROJECT_ROOT)

    assert (PROJECT_ROOT / "reports" / "regression_check.md").exists()
    assert result["status"] == "ok"


def test_phase6_docs_and_reports_exist() -> None:
    assert (PROJECT_ROOT / "docs" / "real_model_eval_guide.md").exists()
    assert (PROJECT_ROOT / "docs" / "cost_control_guide.md").exists()
    assert (PROJECT_ROOT / "docs" / "evaluation_methodology.md").exists()


def test_readme_contains_phase6_positioning() -> None:
    content = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "Claude" in content
    assert "model performance evaluation" in content
    assert "cost control" in content
    assert "Real Provider Eval Is Opt-In" in content
