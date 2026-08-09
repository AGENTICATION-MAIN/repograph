"""
Adversarial Tests: Capability Forgery and Privilege Escalation Prevention.
"""

import pytest
from aegis.capabilities.token import CapabilityToken
from aegis.core.exceptions import CapabilityError, CapabilityScopeViolationError
from aegis.core.types import CapabilityScope, Decision, TaintLevel, ToolExecutionIntent


def test_forged_signature_token_rejection(kernel):
    # Create forged token manually without signing with valid secret key
    forged_token = CapabilityToken(
        token_id="cap-forged-123",
        issuer="kernel",
        subject_agent_id="attacker",
        session_id="session-evil",
        scope=CapabilityScope(allowed_tools={"delete_database"}),
        signature="bad-signature-hex-deadbeef",
    )
    kernel.capabilities._tokens[forged_token.token_id] = forged_token

    intent = ToolExecutionIntent(
        tool_name="delete_database",
        arguments={},
        agent_id="attacker",
        session_id="session-evil",
        capability_token_id=forged_token.token_id,
    )

    res = kernel.verify_intent(intent)
    assert res.decision == Decision.DENY
    assert "Capability violation" in res.reason or "signature" in res.reason.lower()


def test_privilege_escalation_via_attenuation(kernel, secret_key):
    parent = kernel.capabilities.mint_token(
        subject_agent_id="agent-low-priv",
        session_id="session-low",
        allowed_tools={"read_docs"},
        allow_delegation=True,
    )

    # Attempt to derive child token with admin tool
    with pytest.raises(CapabilityScopeViolationError):
        parent.attenuate(
            sub_agent_id="agent-escalated",
            secret_key=secret_key,
            allowed_tools_subset={"execute_bash", "read_docs"},
        )
