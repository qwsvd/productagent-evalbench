from productagent.models import MockProvider


def test_mock_provider_returns_string() -> None:
    provider = MockProvider()

    answer = provider.generate(
        user_query="我可以退款吗？",
        task_type="refund_check",
        expected_answer_points=["需要检查订单"],
        required_tools=["check_order_state"],
        risk_points=["不要承诺一定退款"],
    )

    assert isinstance(answer, str)
    assert answer
    assert "模拟答复" in answer


def test_mock_provider_mentions_context_when_provided() -> None:
    provider = MockProvider()

    answer = provider.generate(
        user_query="会员不能用高级功能怎么办？",
        task_type="membership_check",
        retrieved_context=[
            {
                "source_file": "feature_guide.md",
                "chunk_id": "feature_guide.md#chunk-001",
                "content": "高级功能仅面向有效会员开放。",
                "score": 3,
            }
        ],
    )

    assert "已参考产品文档" in answer
    assert "不编造用户" in answer
