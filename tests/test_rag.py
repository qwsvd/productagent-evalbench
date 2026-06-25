from productagent.agents import RagAgent
from productagent.cli import compare_agents, run_task_set
from productagent.data_loader import PROJECT_ROOT
from productagent.models import MockProvider
from productagent.rag.retriever import SimpleKeywordRetriever


def test_retriever_returns_product_doc_results() -> None:
    retriever = SimpleKeywordRetriever(PROJECT_ROOT / "data" / "product_docs")

    results = retriever.retrieve("会员 高级 功能", top_k=2)

    assert results
    assert len(results) <= 2
    assert {"source_file", "chunk_id", "content", "score"} <= set(results[0])


def test_rag_agent_handles_one_task() -> None:
    agent = RagAgent(provider=MockProvider(), top_k=2)

    result = agent.run(
        task_id="product_rag_test",
        user_query="会员不能用高级功能怎么办",
        task_type="membership_check",
        expected_answer_points=["check member status"],
        required_tools=["check_user_state"],
        risk_points=["do not fabricate user state"],
    )

    assert result["task_id"] == "product_rag_test"
    assert result["agent"] == "rag"
    assert result["provider"] == "mock"
    assert result["retrieved_context"]
    assert "已参考产品文档" in result["final_answer"]


def test_cli_run_rag_writes_results(tmp_path) -> None:
    output_path = tmp_path / "rag_results.jsonl"

    results = run_task_set(
        agent_name="rag",
        provider_name="mock",
        task_set="product_tasks",
        output_path=output_path,
        top_k=2,
    )

    assert len(results) >= 20
    assert output_path.exists()
    assert "retrieved_context" in results[0]
    assert results[0]["retrieved_context"]


def test_cli_compare_generates_report() -> None:
    report_path = compare_agents(
        agent_names=["baseline", "rag"],
        provider_name="mock",
        task_set="product_tasks",
        project_root=PROJECT_ROOT,
        top_k=2,
    )

    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "RAG Comparison Report" in content
    assert "Total tasks" in content
