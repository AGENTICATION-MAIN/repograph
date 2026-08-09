"""
Capability Token Registry and Lifecycle Manager.
"""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Set

from aegis.capabilities.token import CapabilityToken
from aegis.core.exceptions import CapabilityError, CapabilityExpiredError
from aegis.core.types import CapabilityScope, TaintLevel


class CapabilityManager:
    """
    Thread-safe Capability Token Manager.
    Handles token minting, cryptographically secure verification, lifecycle revocation,
    and invocation tracking.
    """

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self._tokens: Dict[str, CapabilityToken] = {}
        self._revocation_list: Set[str] = set()
        self._lock = threading.RLock()

    def mint_token(
        self,
        subject_agent_id: str,
        session_id: str,
        allowed_tools: Set[str],
        forbidden_tools: Optional[Set[str]] = None,
        parameter_rules: Optional[Dict[str, Dict[str, Any]]] = None,
        max_invocations: int = 100,
        ttl_seconds: float = 3600.0,
        max_taint_allowed: TaintLevel = TaintLevel.UNTRUSTED_EXTERNAL,
        rate_limit_per_minute: int = 60,
        allow_delegation: bool = False,
        max_delegation_depth: int = 2,
        issuer: str = "aegis-kernel",
    ) -> CapabilityToken:
        """Mints, signs, and registers a new capability token."""
        now = time.time()
        token_id = f"cap-{uuid.uuid4().hex[:12]}"
        scope = CapabilityScope(
            allowed_tools=set(allowed_tools),
            forbidden_tools=set(forbidden_tools or set()),
            parameter_rules=parameter_rules or {},
            max_invocations=max_invocations,
            invocations_count=0,
            max_taint_allowed=max_taint_allowed,
            rate_limit_per_minute=rate_limit_per_minute,
            allow_delegation=allow_delegation,
            max_delegation_depth=max_delegation_depth,
        )
        token = CapabilityToken(
            token_id=token_id,
            issuer=issuer,
            subject_agent_id=subject_agent_id,
            session_id=session_id,
            scope=scope,
            created_at=now,
            expires_at=now + ttl_seconds,
        )
        token.sign(self.secret_key)

        with self._lock:
            self._tokens[token_id] = token

        return token

    def register_token(self, token: CapabilityToken) -> None:
        """Registers an externally attenuated or created token."""
        with self._lock:
            self._tokens[token.token_id] = token

    def attenuate_token(
        self,
        parent_token_id: str,
        sub_agent_id: str,
        allowed_tools_subset: Optional[Set[str]] = None,
        ttl_seconds: Optional[float] = None,
        max_invocations: Optional[int] = None,
        max_taint_allowed: Optional[TaintLevel] = None,
        parameter_rules_override: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> CapabilityToken:
        """Attenuates a token and automatically registers the child in the registry."""
        with self._lock:
            parent = self._tokens.get(parent_token_id)
            if not parent:
                raise CapabilityError(f"Parent token '{parent_token_id}' not found")
            child = parent.attenuate(
                sub_agent_id=sub_agent_id,
                secret_key=self.secret_key,
                allowed_tools_subset=allowed_tools_subset,
                ttl_seconds=ttl_seconds,
                max_invocations=max_invocations,
                max_taint_allowed=max_taint_allowed,
                parameter_rules_override=parameter_rules_override,
            )
            self._tokens[child.token_id] = child
            return child

    def get_token(self, token_id: str) -> Optional[CapabilityToken]:
        """Retrieves a token by ID."""
        with self._lock:
            return self._tokens.get(token_id)

    def is_revoked(self, token_id: str) -> bool:
        """Checks if token or any of its parent tokens is revoked."""
        with self._lock:
            if token_id in self._revocation_list:
                return True
            token = self._tokens.get(token_id)
            if token and token.parent_token_id:
                return self.is_revoked(token.parent_token_id)
            return False

    def revoke_token(self, token_id: str, reason: str = "Administrative revocation") -> bool:
        """Revokes a token and all its delegated downstream descendants."""
        with self._lock:
            self._revocation_list.add(token_id)
            # Cascade revocation to child tokens
            for child_id, token in list(self._tokens.items()):
                if token.parent_token_id == token_id:
                    self.revoke_token(child_id, reason=f"Parent token {token_id} revoked")
            return True

    def validate_and_consume(
        self,
        token_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        taint_level: TaintLevel,
        current_time: Optional[float] = None,
    ) -> CapabilityToken:
        """
        Validates token, verifies signature, checks revocation, and increments invocation counter.
        """
        with self._lock:
            token = self._tokens.get(token_id)
            if not token:
                raise CapabilityError(f"Capability token '{token_id}' not found in registry.")

            if self.is_revoked(token_id):
                raise CapabilityError(f"Capability token '{token_id}' has been revoked.")

            token.validate_for_execution(
                tool_name=tool_name,
                arguments=arguments,
                taint_level=taint_level,
                secret_key=self.secret_key,
                current_time=current_time,
            )

            token.scope.invocations_count += 1
            return token

    def list_tokens(self, session_id: Optional[str] = None, agent_id: Optional[str] = None) -> List[CapabilityToken]:
        """Lists active tokens matching optional filters."""
        with self._lock:
            result = []
            for token in self._tokens.values():
                if session_id and token.session_id != session_id:
                    continue
                if agent_id and token.subject_agent_id != agent_id:
                    continue
                result.append(token)
            return result

    def prune_expired(self) -> int:
        """Removes expired tokens from the registry."""
        now = time.time()
        pruned = 0
        with self._lock:
            for token_id, token in list(self._tokens.items()):
                if token.is_expired(now):
                    del self._tokens[token_id]
                    pruned += 1
        return pruned
