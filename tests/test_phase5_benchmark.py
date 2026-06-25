import json
from pathlib import Path

from productagent.benchmark_manifest import build_benchmark_manifest, write_benchmark_manifest
from productagent.cli import compare_agents, provider_config_statuses, run_task_set
from productagent.data_loader import PROJECT_ROOT
from productagent.result_schema import validate_report_manifest, validate_result_record
from productagent.run_metadata import create_run_metadata


def test_create_run_metadata_has_required_fields() -> None:
    metadata = create_run_metadata(
        agent_name="tool",
        provider_name="mock",
        task_set="product_tasks",
        eval_mode="mock",
    )

    assert metadata["run_id"]
    assert metadata["provider_mode"] == "mock"
    assert metadata["schema_version"] == "1.0"
    assert metadata["project_phase"] == "Phase 5"


def test_mock_provider_result_record_has_run_metadata(tmp_path: Path) -> None:
    output_path = tmp_path / "tool_mock_results.jsonl"

    results = run_task_set(
        agent_name="tool",
        provider_name="mock",
        task_set="product_tasks",
        output_path=output_path,
        top_k=1,
    )

    first = results[0]
    assert first["run_id"]
    assert first["provider_mode"] == "mock"
    assert first["schema_version"] == "1.0"
    assert first["status"] == "ok"
    assert first["schema_validation"]["valid"] is True


def test_external_missing_key_record_has_provider_mode(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    output_path = tmp_path / "baseline_deepseek_results.jsonl"

    results = run_task_set(
        agent_name="baseline",
        provider_name="deepseek",
        task_set="product_tasks",
        output_path=output_path,
        top_k=1,
    )

    first = results[0]
    assert first["provider_mode"] == "external_missing_key"
    assert first["status"] == "error"
    assert first["error_code"] == "provider_not_configured"


def test_validate_result_record_accepts_legal_record() -> None:
    record = {
        "task_id": "task_001",
        "agent": "tool",
        "provider": "mock",
        "provider_mode": "mock",
        "run_id": "run_001",
        "status": "ok",
        "schema_version": "1.0",
        "answer": "ok",
        "tool_calls": [],
        "route_reason": {},
        "token_usage": {},
    }

    assert validate_result_record(record)["valid"] is True


def test_validate_result_record_reports_missing_task_id() -> None:
    record = {
        "agent": "tool",
        "provider": "mock",
        "provider_mode": "mock",
        "run_id": "run_001",
        "status": "ok",
        "schema_version": "1.0",
        "answer": "ok",
    }

    result = validate_result_record(record)
    assert result["valid"] is False
    assert "missing_field:task_id" in result["errors"]


def test_benchmark_manifest_can_be_generated(tmp_path: Path) -> None:
    manifest = build_benchmark_manifest(
        task_set="product_tasks",
        agents=["baseline", "rag", "tool"],
        provider="mock",
        provider_mode="mock",
        outputs=[PROJECT_ROOT / "outputs" / "tool_mock_results.jsonl"],
        reports=[PROJECT_ROOT / "reports" / "eval_summary.md"],
        project_root=PROJECT_ROOT,
    )
    path = write_benchmark_manifest(manifest, tmp_path / "benchmark_manifest.json")

    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["project"] == "ProductAgent-EvalBench"
    assert validate_report_manifest(loaded)["valid"] is True


def test_mock_compare_generates_phase5_reports() -> None:
    compare_agents(
        agent_names=["baseline", "rag", "tool"],
        provider_name="mock",
        task_set="product_tasks",
        project_root=PROJECT_ROOT,
        top_k=1,
    )

    assert (PROJECT_ROOT / "reports" / "benchmark_manifest.json").exists()
    assert (PROJECT_ROOT / "reports" / "provider_eval_isolation.md").exists()


def test_runbook_exists() -> None:
    assert (PROJECT_ROOT / "docs" / "runbook.md").exists()


def test_readme_has_phase5_positioning() -> None:
    content = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "ProductAgent-EvalBench" in content
    assert "Quick Start" in content
    assert "Provider abstraction" in content
    assert "strict separation between mock eval and external-provider eval" in content


def test_providers_command_statuses_are_local(monkeypatch) -> None:
    for env_name in ["DEEPSEEK_API_KEY", "QWEN_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"]:
        monkeypatch.delenv(env_name, raising=False)

    statuses = provider_config_statuses()

    assert statuses["mock"] == "available"
    assert statuses["deepseek"] == "missing_api_key"
