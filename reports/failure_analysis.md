# Failure Analysis

- Provider mode: mock

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

## Tool Availability Notes

- `tool_selection_error` now means an agent missed a required tool marked `available`.
- `future_mock_unavailable` tools are not counted as strict failures because the MVP intentionally does not implement those integrations.
- `check_order_state` and `check_usage_state` are now available local mock tools and are included in strict scoring.
- `check_risk_state` is now an available local mock tool and is included in strict scoring.
- `route_reason` helps identify whether a low score came from routing, unavailable state, or answer wording.
- Unknown risk state is handled as mock `found: false`; it should prompt verification, not a production conclusion.
- Phase 4 provider support does not change mock-based failure conclusions or claim real-model quality.
- `provider_not_configured`, `provider_request_failed`, `provider_response_invalid`, and `provider_timeout` are provider-layer errors, not automatically Agent logic errors.
- Provider-layer errors should be triaged separately from routing, retrieval, and tool-selection issues.
- Phase 6 model benchmark errors such as `dry_run_external_skipped` and `budget_exceeded` are safety controls, not answer-quality failures.

## Tasks With Future Tools

- No tasks contain future mock unavailable tools.

## Failure Reason Categories

- retrieval_failure: 0
- tool_selection_error: 40
- risk_check_found_issue: 0
- expected_points_not_covered: 0
- mock_provider_expression_gap: 0

## Next Improvements

- Add more task metadata so required tools can match the available local tool set.
- Improve keyword matching for Chinese text and legacy encoded data.
- Add richer mock provider templates for tool-grounded answers.
- Add targeted tests for low-scoring task categories.
- Use `route_reason` to compare expected routing against actual selected tools.
- Run real-provider evaluations separately from mock reports after explicit provider configuration.
