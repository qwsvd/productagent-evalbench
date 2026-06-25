# Failure Analysis

## Low-Scoring Tasks

- baseline / product_001: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_002: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_003: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_004: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_005: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_006: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_007: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_008: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_009: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_010: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_011: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_012: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_013: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_014: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_015: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_016: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_017: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_018: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_019: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- baseline / product_020: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_001: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_002: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_003: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_004: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_005: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_006: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_007: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_008: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_009: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_010: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_011: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_012: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_013: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_014: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_015: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_016: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_017: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_018: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_019: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- rag / product_020: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error
- tool / product_002: success=1.0, tool_accuracy=0.0, risk=0.0; reasons=tool_selection_error

## Tool Availability Notes

- `tool_selection_error` now means an agent missed a required tool marked `available`.
- `future_mock_unavailable` tools are not counted as strict failures because the MVP intentionally does not implement those integrations.

## Tasks With Future Tools

- product_003: check_order_state
- product_005: check_order_state, check_usage_state
- product_006: check_order_state
- product_007: check_order_state
- product_008: check_usage_state
- product_009: check_risk_state

## Failure Reason Categories

- retrieval_failure: 0
- tool_selection_error: 41
- risk_check_found_issue: 0
- expected_points_not_covered: 0
- mock_provider_expression_gap: 0

## Next Improvements

- Add more task metadata so required tools can match the available local tool set.
- Improve keyword matching for Chinese text and legacy encoded data.
- Add richer mock provider templates for tool-grounded answers.
- Add targeted tests for low-scoring task categories.
