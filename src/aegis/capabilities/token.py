"""
Capability Token Implementation for AegisKernel.

Provides cryptographically signed, attenuable capability tokens for fine-grained,
least-privilege agent execution.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from aegis.core.exceptions import (
    CapabilityError,
    CapabilityExpiredError,
    CapabilityScopeViolationError,
)
from aegis.core.types import CapabilityScope, TaintLevel


@dataclass
class CapabilityToken:
    """
    Cryptographically verifiable capability token.
    Represents an unforgeable authorization lease granting an agent specific privileges.
    """
    token_id: str
    issuer: str
    subject_agent_id: str
    session_id: str
    scope: CapabilityScope
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 3600.0)  # 1 hour default
    parent_token_id: Optional[str] = None
    delegation_depth: int = 0
    signature: str = ""

    def canonical_bytes(self) -> bytes:
        """
        Returns deterministic canonical byte representation of immutable token fields
        for cryptographic signing.
        """
        canonical_scope = {
            "allowed_tools": sorted(list(self.scope.allowed_tools)),
            "forbidden_tools": sorted(list(self.scope.forbidden_tools)),
            "parameter_rules": self.scope.parameter_rules,
            "max_invocations": self.scope.max_invocations,
            "max_taint_allowed": self.scope.max_taint_allowed.name,
            "rate_limit_per_minute": self.scope.rate_limit_per_minute,
            "allow_delegation": self.scope.allow_delegation,
            "max_delegation_depth": self.scope.max_delegation_depth,
        }
        canonical_dict = {
            "token_id": self.token_id,
            "issuer": self.issuer,
            "subject_agent_id": self.subject_agent_id,
            "session_id": self.session_id,
            "scope": canonical_scope,
            "created_at": round(self.created_at, 4),
            "expires_at": round(self.expires_at, 4),
            "parent_token_id": self.parent_token_id,
            "delegation_depth": self.delegation_depth,
        }
        return json.dumps(canonical_dict, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def sign(self, secret_key: str) -> str:
        """Signs the token using HMAC-SHA256."""
        sig = hmac.new(
            secret_key.encode("utf-8"),
            self.canonical_bytes(),
            hashlib.sha256
        ).hexdigest()
        self.signature = sig
        return sig

    def verify_signature(self, secret_key: str) -> bool:
        """Verifies the HMAC-SHA256 signature."""
        if not self.signature:
            return False
        expected_sig = hmac.new(
            secret_key.encode("utf-8"),
            self.canonical_bytes(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(self.signature, expected_sig)

    def is_expired(self, current_time: Optional[float] = None) -> bool:
        """Checks whether the token has expired."""
        now = current_time if current_time is not None else time.time()
        return now >= self.expires_at

    def validate_for_execution(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        taint_level: TaintLevel,
        secret_key: str,
        current_time: Optional[float] = None,
    ) -> None:
        """
        Validates token validity, cryptographic signature, scope, invocations, and taint ceilings.
        Raises specific CapabilityError subtypes if validation fails.
        """
        if not self.verify_signature(secret_key):
            raise CapabilityError("Invalid cryptographic signature on capability token.")

        if self.is_expired(current_time):
            raise CapabilityExpiredError(
                f"Capability token '{self.token_id}' expired at {self.expires_at}."
            )

        if self.scope.invocations_count >= self.scope.max_invocations:
            raise CapabilityScopeViolationError(
                f"Capability token invocation limit ({self.scope.max_invocations}) exceeded."
            )

        if not self.scope.is_tool_allowed(tool_name):
            raise CapabilityScopeViolationError(
                f"Tool '{tool_name}' is not permitted by capability scope. Allowed: {sorted(list(self.scope.allowed_tools))}"
            )

        if taint_level.value > self.scope.max_taint_allowed.value:
            raise CapabilityScopeViolationError(
                f"Execution taint level ({taint_level.name}) exceeds maximum allowed ({self.scope.max_taint_allowed.name})."
            )

        # Validate parameter constraint rules if defined
        if tool_name in self.scope.parameter_rules:
            rules = self.scope.parameter_rules[tool_name]
            for param_key, expected_spec in rules.items():
                if param_key in arguments:
                    val = arguments[param_key]
                    if isinstance(expected_spec, dict):
                        if "max" in expected_spec and isinstance(val, (int, float)):
                            if val > expected_spec["max"]:
                                raise CapabilityScopeViolationError(
                                    f"Parameter '{param_key}' value {val} exceeds allowed maximum {expected_spec['max']}."
                                )
                        if "min" in expected_spec and isinstance(val, (int, float)):
                            if val < expected_spec["min"]:
                                raise CapabilityScopeViolationError(
                                    f"Parameter '{param_key}' value {val} is below allowed minimum {expected_spec['min']}."
                                )
                        if "allowed_values" in expected_spec:
                            if val not in expected_spec["allowed_values"]:
                                raise CapabilityScopeViolationError(
                                    f"Parameter '{param_key}' value '{val}' not in allowed set: {expected_spec['allowed_values']}."
                                )

    def attenuate(
        self,
        sub_agent_id: str,
        secret_key: str,
        allowed_tools_subset: Optional[Set[str]] = None,
        ttl_seconds: Optional[float] = None,
        max_invocations: Optional[int] = None,
        max_taint_allowed: Optional[TaintLevel] = None,
        parameter_rules_override: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> CapabilityToken:
        """
        Creates a child token with strictly attenuated (narrowed or equal) privileges.
        Privileges can NEVER be widened during attenuation (Capability Safety Invariant).
        """
        if not self.scope.allow_delegation:
            raise CapabilityScopeViolationError("Token does not permit delegation.")

        if self.delegation_depth >= self.scope.max_delegation_depth:
            raise CapabilityScopeViolationError(
                f"Maximum delegation depth ({self.scope.max_delegation_depth}) reached."
            )

        # Calculate attenuated tool set
        if allowed_tools_subset is not None:
            if "*" not in self.scope.allowed_tools:
                for tool in allowed_tools_subset:
                    if tool not in self.scope.allowed_tools:
                        raise CapabilityScopeViolationError(
                            f"Cannot grant tool '{tool}' not present in parent capability."
                        )
            effective_tools = allowed_tools_subset
        else:
            effective_tools = set(self.scope.allowed_tools)

        # Expiration cannot exceed parent expiration
        now = time.time()
        parent_remaining = max(0.0, self.expires_at - now)
        requested_ttl = ttl_seconds if ttl_seconds is not None else parent_remaining
        effective_expires_at = min(self.expires_at, now + requested_ttl)

        # Invocations cannot exceed parent remaining invocations
        parent_remaining_inv = max(0, self.scope.max_invocations - self.scope.invocations_count)
        if max_invocations is not None:
            effective_max_inv = min(max_invocations, parent_remaining_inv)
        else:
            effective_max_inv = parent_remaining_inv

        # Taint level can only be more restrictive (lower value)
        if max_taint_allowed is not None:
            effective_taint = min(max_taint_allowed, self.scope.max_taint_allowed, key=lambda t: t.value)
        else:
            effective_taint = self.scope.max_taint_allowed

        merged_param_rules = dict(self.scope.parameter_rules)
        if parameter_rules_override:
            merged_param_rules.update(parameter_rules_override)

        child_scope = CapabilityScope(
            allowed_tools=effective_tools,
            forbidden_tools=set(self.scope.forbidden_tools),
            parameter_rules=merged_param_rules,
            max_invocations=effective_max_inv,
            invocations_count=0,
            max_taint_allowed=effective_taint,
            rate_limit_per_minute=self.scope.rate_limit_per_minute,
            allow_delegation=self.scope.allow_delegation,
            max_delegation_depth=self.scope.max_delegation_depth,
        )

        child_token = CapabilityToken(
            token_id=f"cap-{uuid.uuid4().hex[:12]}",
            issuer=f"agent:{self.subject_agent_id}",
            subject_agent_id=sub_agent_id,
            session_id=self.session_id,
            scope=child_scope,
            created_at=now,
            expires_at=effective_expires_at,
            parent_token_id=self.token_id,
            delegation_depth=self.delegation_depth + 1,
        )
        child_token.sign(secret_key)
        return child_token

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "issuer": self.issuer,
            "subject_agent_id": self.subject_agent_id,
            "session_id": self.session_id,
            "scope": self.scope.to_dict(),
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "parent_token_id": self.parent_token_id,
            "delegation_depth": self.delegation_depth,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CapabilityToken:
        token = cls(
            token_id=data["token_id"],
            issuer=data["issuer"],
            subject_agent_id=data["subject_agent_id"],
            session_id=data["session_id"],
            scope=CapabilityScope.from_dict(data["scope"]),
            created_at=data.get("created_at", time.time()),
            expires_at=data.get("expires_at", time.time() + 3600.0),
            parent_token_id=data.get("parent_token_id"),
            delegation_depth=data.get("delegation_depth", 0),
            signature=data.get("signature", ""),
        )
        return token
