"""
Unit tests for Policy Parser and Policy Engine.
"""

import pytest
from aegis.core.types import Decision, PolicyPhase, Severity, ToolExecutionIntent
from aegis.policy.engine import PolicyEngine
from aegis.policy.parser import PolicyParser


def test_rule_parsing_and_evaluation():
    engine = PolicyEngine()

    rule_dict = {
        "rule_id": "RULE_TRANSFER_LIMIT",
        "rule_name": "Maximum Transfer Limit",
        "description": "Transfer amount cannot exceed 5000",
        "phase": "PRE_EXECUTION",
        "condition": {
            "field": "args.amount",
            "op": "<=",
            "value": 5000,
        },
        "target_tools": ["transfer_funds"],
        "action_on_violation": "DENY",
        "severity": "HIGH",
    }

    rule = PolicyParser.parse_rule(rule_dict)
    engine.register_rule(rule)

    # Valid intent
    intent1 = ToolExecutionIntent(
        tool_name="transfer_funds",
        arguments={"amount": 2500},
        agent_id="agent-1",
        session_id="session-1",
    )
    decision1, violations1, latency1, count1 = engine.evaluate_intent(intent1)
    assert decision1 == Decision.ALLOW
    assert len(violations1) == 0
    assert count1 == 1

    # Invariant violating intent
    intent2 = ToolExecutionIntent(
        tool_name="transfer_funds",
        arguments={"amount": 9000},
        agent_id="agent-1",
        session_id="session-1",
    )
    decision2, violations2, latency2, count2 = engine.evaluate_intent(intent2)
    assert decision2 == Decision.DENY
    assert len(violations2) == 1
    assert violations2[0].rule_id == "RULE_TRANSFER_LIMIT"


def test_complex_and_or_nested_rules():
    engine = PolicyEngine()

    # Rule: user must be admin OR (amount <= 100 AND currency == 'USD')
    rule = PolicyParser.parse_rule({
        "rule_id": "RULE_TIERED_PERMISSIONS",
        "rule_name": "Tiered Permissions Rule",
        "description": "Admin or small USD transaction",
        "phase": "PRE_EXECUTION",
        "condition": {
            "or": [
                {"field": "session.user_role", "op": "==", "value": "admin"},
                {
                    "and": [
                        {"field": "args.amount", "op": "<=", "value": 100},
                        {"field": "args.currency", "op": "==", "value": "USD"},
                    ]
                }
            ]
        },
        "target_tools": ["process_payment"],
        "action_on_violation": "DENY",
    })
    engine.register_rule(rule)

    # Regular user with $50 USD -> ALLOW
    intent1 = ToolExecutionIntent(
        tool_name="process_payment",
        arguments={"amount": 50, "currency": "USD"},
        agent_id="agent-1",
        session_id="session-1",
    )
    dec1, _, _, _ = engine.evaluate_intent(intent1, session_context={"user_role": "guest"})
    assert dec1 == Decision.ALLOW

    # Regular user with $500 EUR -> DENY
    intent2 = ToolExecutionIntent(
        tool_name="process_payment",
        arguments={"amount": 500, "currency": "EUR"},
        agent_id="agent-1",
        session_id="session-1",
    )
    dec2, viols2, _, _ = engine.evaluate_intent(intent2, session_context={"user_role": "guest"})
    assert dec2 == Decision.DENY
    assert len(viols2) == 1

    # Admin with $500 EUR -> ALLOW
    dec3, _, _, _ = engine.evaluate_intent(intent2, session_context={"user_role": "admin"})
    assert dec3 == Decision.ALLOW
