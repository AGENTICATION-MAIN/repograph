"""
Pactum Core Types & Data Models.

Defines the mathematical primitives for Coasian Micro-Resource Bartering,
Fractional Capability Units (FCUs), Marginal Utility Functions,
and Closed-Form Nash Bargaining Equilibria.
"""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union


class ResourceType(str, enum.Enum):
    """Types of consumable, time-decaying computational capabilities."""
    API_RATE_LIMIT = "API_RATE_LIMIT"               # Requests per second/minute (e.g. Stripe, OpenAI, GitHub)
    QUEUE_PRIORITY_SLOT = "QUEUE_PRIORITY_SLOT"     # Priority queue execution leases
    GPU_VRAM_MB_SEC = "GPU_VRAM_MB_SEC"             # GPU memory-time slices (MB * seconds)
    CACHE_RESIDENCY_SLOT = "CACHE_RESIDENCY_SLOT"   # High-speed Redis/Memcached cache residency
    DATABASE_CONN_LEASE = "DATABASE_CONN_LEASE"     # Ephemeral database pool connection slots
    BURST_CPU_CREDIT = "BURST_CPU_CREDIT"           # Burst CPU compute credits


class UtilityFunctionType(str, enum.Enum):
    """Mathematical utility curve classifications."""
    CONCAVE_LOGARITHMIC = "CONCAVE_LOGARITHMIC"     # U(x) = alpha * ln(1 + beta * x) (Diminishing marginal returns)
    PIECEWISE_LINEAR = "PIECEWISE_LINEAR"           # Step-wise urgency (e.g. threshold needed to avoid timeout)
    EXPONENTIAL_URGENCY = "EXPONENTIAL_URGENCY"     # U(x) = alpha * (1 - e^(-beta * x))


class LeaseStatus(str, enum.Enum):
    """Lifecycle state of an ephemeral capability lease."""
    ACTIVE = "ACTIVE"
    CONSUMED = "CONSUMED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    DISPUTED = "DISPUTED"


@dataclass
class UtilityProfile:
    """
    Continuous marginal utility curve exposed by a service for a specific resource type.
    Represents U(x): how much utility (operational value) the service gains from quantity x.
    """
    function_type: UtilityFunctionType
    alpha: float = 1.0                              # Scaling factor / weight of urgency
    beta: float = 0.1                               # Saturation curvature parameter
    reservation_utility: float = 0.0                # Disagreement point d: baseline utility if no trade occurs
    max_capacity_needed: float = 1000.0             # Saturation ceiling beyond which marginal utility is 0

    def evaluate(self, quantity: float) -> float:
        """Evaluates total utility U(quantity)."""
        if quantity <= 0.0:
            return self.reservation_utility
        q = min(quantity, self.max_capacity_needed)
        if self.function_type == UtilityFunctionType.CONCAVE_LOGARITHMIC:
            import math
            return self.alpha * math.log(1.0 + self.beta * q)
        elif self.function_type == UtilityFunctionType.EXPONENTIAL_URGENCY:
            import math
            return self.alpha * (1.0 - math.exp(-self.beta * q))
        elif self.function_type == UtilityFunctionType.PIECEWISE_LINEAR:
            return self.alpha * q
        return self.alpha * q

    def marginal_utility(self, current_quantity: float, delta: float) -> float:
        """Computes marginal utility gain ΔU = U(q + Δq) - U(q)."""
        return self.evaluate(current_quantity + delta) - self.evaluate(current_quantity)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "function_type": self.function_type.value,
            "alpha": self.alpha,
            "beta": self.beta,
            "reservation_utility": self.reservation_utility,
            "max_capacity_needed": self.max_capacity_needed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UtilityProfile:
        return cls(
            function_type=UtilityFunctionType(data["function_type"]),
            alpha=float(data.get("alpha", 1.0)),
            beta=float(data.get("beta", 0.1)),
            reservation_utility=float(data.get("reservation_utility", 0.0)),
            max_capacity_needed=float(data.get("max_capacity_needed", 1000.0)),
        )


@dataclass
class CapabilityToken:
    """
    Cryptographically verifiable capability asset owned by a service.
    Represents an unconsumed slice of computing capability.
    """
    token_id: str
    resource_type: ResourceType
    owner_service_id: str
    total_quantity: float
    available_quantity: float
    time_to_live_seconds: float
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 60.0)
    metadata: Dict[str, Any] = field(default_factory=dict)
    signature: str = ""

    def is_expired(self, current_time: Optional[float] = None) -> bool:
        now = current_time if current_time is not None else time.time()
        return now >= self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "resource_type": self.resource_type.value,
            "owner_service_id": self.owner_service_id,
            "total_quantity": self.total_quantity,
            "available_quantity": self.available_quantity,
            "time_to_live_seconds": self.time_to_live_seconds,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "metadata": self.metadata,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CapabilityToken:
        return cls(
            token_id=data["token_id"],
            resource_type=ResourceType(data["resource_type"]),
            owner_service_id=data["owner_service_id"],
            total_quantity=float(data["total_quantity"]),
            available_quantity=float(data["available_quantity"]),
            time_to_live_seconds=float(data.get("time_to_live_seconds", 60.0)),
            created_at=float(data.get("created_at", time.time())),
            expires_at=float(data.get("expires_at", time.time() + 60.0)),
            metadata=data.get("metadata", {}),
            signature=data.get("signature", ""),
        )


@dataclass
class BarterOffer:
    """
    A bilateral or multilateral barter proposal submitted to the negotiation engine.
    """
    offer_id: str
    proposer_service_id: str
    offered_resource_type: ResourceType
    offered_quantity: float
    requested_resource_type: ResourceType
    min_requested_quantity: float
    proposer_utility_profile: UtilityProfile
    ttl_seconds: float = 30.0
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "offer_id": self.offer_id,
            "proposer_service_id": self.proposer_service_id,
            "offered_resource_type": self.offered_resource_type.value,
            "offered_quantity": self.offered_quantity,
            "requested_resource_type": self.requested_resource_type.value,
            "min_requested_quantity": self.min_requested_quantity,
            "proposer_utility_profile": self.proposer_utility_profile.to_dict(),
            "ttl_seconds": self.ttl_seconds,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BarterOffer:
        return cls(
            offer_id=data["offer_id"],
            proposer_service_id=data["proposer_service_id"],
            offered_resource_type=ResourceType(data["offered_resource_type"]),
            offered_quantity=float(data["offered_quantity"]),
            requested_resource_type=ResourceType(data["requested_resource_type"]),
            min_requested_quantity=float(data["min_requested_quantity"]),
            proposer_utility_profile=UtilityProfile.from_dict(data["proposer_utility_profile"]),
            ttl_seconds=float(data.get("ttl_seconds", 30.0)),
            created_at=float(data.get("created_at", time.time())),
            metadata=data.get("metadata", {}),
        )


@dataclass
class BargainingAgreement:
    """
    A mathematically proven Pareto-optimal Nash Bargaining Agreement between two services.
    """
    agreement_id: str
    party_a_id: str
    party_b_id: str
    resource_a_to_b_type: ResourceType
    quantity_a_to_b: float
    resource_b_to_a_type: ResourceType
    quantity_b_to_a: float
    nash_product: float
    surplus_utility_a: float
    surplus_utility_b: float
    is_pareto_optimal: bool
    solving_latency_us: float                     # Microseconds taken to compute closed-form solution
    timestamp: float = field(default_factory=time.time)
    lease_a_id: Optional[str] = None
    lease_b_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agreement_id": self.agreement_id,
            "party_a_id": self.party_a_id,
            "party_b_id": self.party_b_id,
            "resource_a_to_b_type": self.resource_a_to_b_type.value,
            "quantity_a_to_b": self.quantity_a_to_b,
            "resource_b_to_a_type": self.resource_b_to_a_type.value,
            "quantity_b_to_a": self.quantity_b_to_a,
            "nash_product": self.nash_product,
            "surplus_utility_a": self.surplus_utility_a,
            "surplus_utility_b": self.surplus_utility_b,
            "is_pareto_optimal": self.is_pareto_optimal,
            "solving_latency_us": self.solving_latency_us,
            "timestamp": self.timestamp,
            "lease_a_id": self.lease_a_id,
            "lease_b_id": self.lease_b_id,
        }


@dataclass
class AtomicLease:
    """
    An ephemeral execution lease minted as the atomic settlement of a bargaining agreement.
    Provides verified proxy authorization to consume the bartered capability.
    """
    lease_id: str
    agreement_id: str
    resource_type: ResourceType
    granter_service_id: str
    grantee_service_id: str
    allocated_quantity: float
    consumed_quantity: float = 0.0
    starts_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 60.0)
    status: LeaseStatus = LeaseStatus.ACTIVE
    signature: str = ""

    def is_valid(self, current_time: Optional[float] = None) -> bool:
        now = current_time if current_time is not None else time.time()
        return (
            self.status == LeaseStatus.ACTIVE
            and now < self.expires_at
            and self.consumed_quantity < self.allocated_quantity
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lease_id": self.lease_id,
            "agreement_id": self.agreement_id,
            "resource_type": self.resource_type.value,
            "granter_service_id": self.granter_service_id,
            "grantee_service_id": self.grantee_service_id,
            "allocated_quantity": self.allocated_quantity,
            "consumed_quantity": self.consumed_quantity,
            "starts_at": self.starts_at,
            "expires_at": self.expires_at,
            "status": self.status.value,
            "signature": self.signature,
        }
