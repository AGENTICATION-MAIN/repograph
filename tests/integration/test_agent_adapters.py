"""
Integration tests for OpenAI and Anthropic Agent Adapters and @aegis_guard decorator.
"""

import json
import pytest
from aegis.adapters.anthropic_adapter import AnthropicToolAdapter
from aegis.adapters.decorator import aegis_guard
from aegis.adapters.openai_adapter import OpenAIToolAdapter
from aegis.core.exceptions import InvariantBreachError
from aegis.core.types import Decision, PolicyPhase
from aegis.policy.parser import PolicyParser


def test_openai_tool_adapter_allowed_and_blocked(kernel):
    adapter = OpenAIToolAdapter(kernel)

    # Register rule: max order quantity is 50
    rule = PolicyParser.parse_rule({
        "rule_id": "RULE_MAX_QTY",
        "rule_name": "Maximum Order Quantity",
        "description": "Quantity cannot exceed 50",
        "phase": "PRE_EXECUTION",
        "condition": {"field": "args.quantity", "op": "<=", "value": 50},
        "target_tools": ["place_order"],
    })
    kernel.policies.register_rule(rule)

    # Allowed OpenAI call
    valid_call = {
        "id": "call_12345",
        "type": "function",
        "function": {
            "name": "place_order",
            "arguments": json.dumps({"item": "widget", "quantity": 10}),
        }
    }
    res_val, out_val = adapter.intercept_and_verify(
        valid_call,
        agent_id="agent-ecom",
        session_id="session-ecom",
    )
    assert res_val.decision == Decision.ALLOW
    assert out_val["id"] == "call_12345"

    # Blocked OpenAI call (quantity 100)
    blocked_call = {
        "id": "call_99999",
        "type": "function",
        "function": {
            "name": "place_order",
            "arguments": json.dumps({"item": "widget", "quantity": 100}),
        }
    }
    res_blk, out_blk = adapter.intercept_and_verify(
        blocked_call,
        agent_id="agent-ecom",
        session_id="session-ecom",
    )
    assert res_blk.decision == Decision.DENY
    assert out_blk["role"] == "tool"
    assert "REJECTED_BY_AEGIS_KERNEL" in out_blk["content"]


def test_anthropic_tool_adapter(kernel):
    adapter = AnthropicToolAdapter(kernel)

    raw_tool_use = {
        "type": "tool_use",
        "id": "toolu_01A",
        "name": "lookup_user",
        "input": {"user_id": "USR-400"}
    }
    res, out = adapter.intercept_and_verify(
        raw_tool_use,
        agent_id="claude-agent",
        session_id="session-claude",
    )
    assert res.decision == Decision.ALLOW
    assert out["id"] == "toolu_01A"


def test_aegis_guard_decorator(kernel):
    # Register rule: amount must be > 0
    rule = PolicyParser.parse_rule({
        "rule_id": "RULE_POSITIVE_AMT",
        "rule_name": "Positive Amount",
        "description": "Amount must be positive",
        "phase": "PRE_EXECUTION",
        "condition": {"field": "args.amount", "op": ">", "value": 0},
        "target_tools": ["send_payment"],
    })
    kernel.policies.register_rule(rule)

    @aegis_guard(kernel=kernel, tool_name="send_payment")
    def send_payment(recipient: str, amount: float):
        return f"Paid {recipient} ${amount}"

    # Valid call
    msg = send_payment("alice", 50.0)
    assert msg == "Paid alice $50.0"

    # Invalid call should raise InvariantBreachError
    with pytest.raises(InvariantBreachError):
        send_payment("bob", -10.0)
