"""
Unit tests for Shadow State Sandbox and State Invariants.
"""

import pytest
from aegis.core.types import ToolExecutionIntent
from aegis.simulation.invariants import StateInvariant
from aegis.simulation.sandbox import ShadowSandbox


def test_shadow_simulation_and_diff():
    sandbox = ShadowSandbox(initial_state={
        "accounts": {
            "ACC-1": {"balance": 500.0},
            "ACC-2": {"balance": 200.0},
        }
    })

    intent = ToolExecutionIntent(
        tool_name="update_account_balance",
        arguments={"account_id": "ACC-1", "amount": -100.0},
        agent_id="agent-1",
        session_id="session-1",
    )

    success, violations, diff, sim_state = sandbox.simulate_and_verify(intent)
    assert success is True
    assert len(violations) == 0
    assert sim_state["accounts"]["ACC-1"]["balance"] == 400.0
    assert "modified" in diff


def test_non_negative_balance_invariant_breach():
    sandbox = ShadowSandbox(initial_state={
        "accounts": {
            "ACC-1": {"balance": 50.0},
        }
    })

    # Attempt to withdraw $200 (would result in -150)
    intent = ToolExecutionIntent(
        tool_name="update_account_balance",
        arguments={"account_id": "ACC-1", "amount": -200.0},
        agent_id="agent-1",
        session_id="session-1",
    )

    success, violations, diff, sim_state = sandbox.simulate_and_verify(intent)
    assert success is False
    assert len(violations) >= 1
    assert violations[0].rule_id == "INV_NON_NEGATIVE_BALANCE"
