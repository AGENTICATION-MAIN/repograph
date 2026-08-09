"""
Unit tests for Capability Tokens and Capability Manager.
"""

import time
import pytest
from aegis.capabilities.manager import CapabilityManager
from aegis.capabilities.token import CapabilityToken
from aegis.core.exceptions import (
    CapabilityError,
    CapabilityExpiredError,
    CapabilityScopeViolationError,
)
from aegis.core.types import CapabilityScope, TaintLevel


def test_token_minting_and_signature(secret_key):
    manager = CapabilityManager(secret_key=secret_key)
    token = manager.mint_token(
        subject_agent_id="agent-007",
        session_id="session-alpha",
        allowed_tools={"query_db", "fetch_url"},
        max_invocations=5,
        ttl_seconds=60.0,
    )

    assert token.token_id.startswith("cap-")
    assert token.subject_agent_id == "agent-007"
    assert token.verify_signature(secret_key) is True
    assert token.verify_signature("wrong-key") is False


def test_token_expiration(secret_key):
    manager = CapabilityManager(secret_key=secret_key)
    token = manager.mint_token(
        subject_agent_id="agent-007",
        session_id="session-alpha",
        allowed_tools={"query_db"},
        ttl_seconds=1.0,
    )

    # Valid now
    token.validate_for_execution("query_db", {}, TaintLevel.SYSTEM, secret_key)

    # Fast forward in validation
    with pytest.raises(CapabilityExpiredError):
        token.validate_for_execution("query_db", {}, TaintLevel.SYSTEM, secret_key, current_time=time.time() + 10.0)


def test_token_scope_violations(secret_key):
    manager = CapabilityManager(secret_key=secret_key)
    token = manager.mint_token(
        subject_agent_id="agent-007",
        session_id="session-alpha",
        allowed_tools={"query_db"},
        parameter_rules={
            "query_db": {"limit": {"max": 100}}
        },
        max_taint_allowed=TaintLevel.AUTHENTICATED_USER,
    )

    # Unauthorized tool
    with pytest.raises(CapabilityScopeViolationError, match="not permitted"):
        token.validate_for_execution("delete_db", {}, TaintLevel.SYSTEM, secret_key)

    # Parameter limit exceeded
    with pytest.raises(CapabilityScopeViolationError, match="exceeds allowed maximum"):
        token.validate_for_execution("query_db", {"limit": 500}, TaintLevel.SYSTEM, secret_key)

    # Taint level exceeded
    with pytest.raises(CapabilityScopeViolationError, match="exceeds maximum allowed"):
        token.validate_for_execution("query_db", {"limit": 50}, TaintLevel.UNTRUSTED_EXTERNAL, secret_key)


def test_token_attenuation_safety_invariant(secret_key):
    manager = CapabilityManager(secret_key=secret_key)
    parent = manager.mint_token(
        subject_agent_id="parent-agent",
        session_id="session-alpha",
        allowed_tools={"read_file", "write_file"},
        allow_delegation=True,
        max_delegation_depth=2,
        max_invocations=10,
    )

    # Attenuate into sub-token with only 'read_file'
    child = parent.attenuate(
        sub_agent_id="child-agent",
        secret_key=secret_key,
        allowed_tools_subset={"read_file"},
        max_invocations=3,
    )

    assert child.subject_agent_id == "child-agent"
    assert child.scope.allowed_tools == {"read_file"}
    assert child.scope.max_invocations == 3
    assert child.delegation_depth == 1
    assert child.verify_signature(secret_key) is True

    # Escalation attempt: Child cannot request tool not present in parent
    with pytest.raises(CapabilityScopeViolationError, match="Cannot grant tool"):
        parent.attenuate(
            sub_agent_id="malicious-child",
            secret_key=secret_key,
            allowed_tools_subset={"delete_all_files"},
        )


def test_token_revocation_cascade(secret_key):
    manager = CapabilityManager(secret_key=secret_key)
    parent = manager.mint_token(
        subject_agent_id="parent-agent",
        session_id="session-alpha",
        allowed_tools={"tool_a"},
        allow_delegation=True,
    )
    child = manager.attenuate_token(parent.token_id, "child-agent")

    # Revoke parent
    manager.revoke_token(parent.token_id)
    assert manager.is_revoked(parent.token_id) is True
    assert manager.is_revoked(child.token_id) is True

    with pytest.raises(CapabilityError, match="revoked"):
        manager.validate_and_consume(parent.token_id, "tool_a", {}, TaintLevel.SYSTEM)
