"""
Adversarial Tests: Parameter Fuzzing, Edge Cases, and Malformed Payloads.
"""

import pytest
from aegis.core.types import Decision, ToolExecutionIntent


@pytest.mark.parametrize("fuzz_args", [
    {"amount": float("inf")},
    {"amount": float("nan")},
    {"nested": {"deep": {"level_5": {"key": "value" * 1000}}}},
    {"unicode_payload": "こんにちは\x00\x01\x02\r\n\t"},
    {"sql_frag": "1' OR '1'='1' -- "},
    {"overflow_int": 2**128},
])
def test_parameter_fuzzing_resilience(kernel, fuzz_args):
    intent = ToolExecutionIntent(
        tool_name="generic_tool",
        arguments=fuzz_args,
        agent_id="fuzz-tester",
        session_id="fuzz-session",
    )

    # Must never crash the kernel with an unhandled runtime exception
    result = kernel.verify_intent(intent)
    assert result.decision in (Decision.ALLOW, Decision.DENY, Decision.QUARANTINE)
    assert result.merkle_node_hash is not None
