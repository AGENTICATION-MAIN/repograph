"""
Capability Vault and Asset Management for Pactum.

Handles local capability minting, cryptographic signing, reservation locks,
and fractional token allocation.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import threading
import time
import uuid
from typing import Dict, List, Optional, Set

from pactum.core.exceptions import InsufficientCapabilityError
from pactum.core.types import CapabilityToken, ResourceType


def compute_token_signature(token: CapabilityToken, secret_key: str) -> str:
    """Computes HMAC-SHA256 signature over canonical token descriptor."""
    canonical = {
        "token_id": token.token_id,
        "resource_type": token.resource_type.value,
        "owner_service_id": token.owner_service_id,
        "total_quantity": token.total_quantity,
        "time_to_live_seconds": token.time_to_live_seconds,
        "created_at": round(token.created_at, 4),
        "expires_at": round(token.expires_at, 4),
    }
    raw = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(secret_key.encode("utf-8"), raw, hashlib.sha256).hexdigest()


class CapabilityVault:
    """
    Thread-Safe Local Capability Asset Vault.
    Maintains a service's owned capability tokens, tracks reservations, and enforces limits.
    """

    def __init__(self, service_id: str, secret_key: str):
        self.service_id = service_id
        self.secret_key = secret_key
        self._tokens: Dict[str, CapabilityToken] = {}
        self._reserved_amounts: Dict[str, float] = {}  # token_id -> reserved_amount
        self._lock = threading.RLock()

    def mint_capability(
        self,
        resource_type: ResourceType,
        quantity: float,
        ttl_seconds: float = 300.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CapabilityToken:
        """Mints a newly owned capability asset and signs it."""
        now = time.time()
        token = CapabilityToken(
            token_id=f"cap-{uuid.uuid4().hex[:12]}",
            resource_type=resource_type,
            owner_service_id=self.service_id,
            total_quantity=quantity,
            available_quantity=quantity,
            time_to_live_seconds=ttl_seconds,
            created_at=now,
            expires_at=now + ttl_seconds,
            metadata=metadata or {},
        )
        token.signature = compute_token_signature(token, self.secret_key)

        with self._lock:
            self._tokens[token.token_id] = token
            self._reserved_amounts[token.token_id] = 0.0

        return token

    def get_available_quantity(self, resource_type: ResourceType) -> float:
        """Returns total unreserved, unexpired quantity available for a resource type."""
        now = time.time()
        with self._lock:
            total = 0.0
            for token in self._tokens.values():
                if token.resource_type == resource_type and not token.is_expired(now):
                    reserved = self._reserved_amounts.get(token.token_id, 0.0)
                    avail = max(0.0, token.available_quantity - reserved)
                    total += avail
            return total

    def reserve_quantity(self, resource_type: ResourceType, requested_amount: float) -> List[Tuple[str, float]]:
        """
        Reserves requested amount across available tokens.
        Returns list of (token_id, reserved_from_token).
        Raises InsufficientCapabilityError if unavailable.
        """
        now = time.time()
        with self._lock:
            total_avail = self.get_available_quantity(resource_type)
            if total_avail < requested_amount:
                raise InsufficientCapabilityError(
                    f"Service '{self.service_id}' has only {total_avail:.2f} {resource_type.value} available, "
                    f"cannot reserve {requested_amount:.2f}."
                )

            remaining_to_reserve = requested_amount
            allocations = []

            for token in self._tokens.values():
                if token.resource_type == resource_type and not token.is_expired(now):
                    reserved = self._reserved_amounts.get(token.token_id, 0.0)
                    avail = max(0.0, token.available_quantity - reserved)
                    if avail > 0:
                        take = min(avail, remaining_to_reserve)
                        self._reserved_amounts[token.token_id] = reserved + take
                        allocations.append((token.token_id, take))
                        remaining_to_reserve -= take
                        if remaining_to_reserve <= 0:
                            break

            return allocations

    def release_reservation(self, allocations: List[Tuple[str, float]]) -> None:
        """Releases previously locked reservations."""
        with self._lock:
            for token_id, amount in allocations:
                if token_id in self._reserved_amounts:
                    self._reserved_amounts[token_id] = max(0.0, self._reserved_amounts[token_id] - amount)

    def commit_reservation_to_lease(self, allocations: List[Tuple[str, float]]) -> float:
        """Permanently deducts reserved quantity from token availability when lease executes."""
        with self._lock:
            total_committed = 0.0
            for token_id, amount in allocations:
                if token_id in self._tokens:
                    token = self._tokens[token_id]
                    token.available_quantity = max(0.0, token.available_quantity - amount)
                    self._reserved_amounts[token_id] = max(0.0, self._reserved_amounts.get(token_id, 0.0) - amount)
                    total_committed += amount
            return total_committed

    def list_tokens(self) -> List[CapabilityToken]:
        with self._lock:
            return list(self._tokens.values())
