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