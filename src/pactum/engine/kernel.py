"""
Unified Pactum Kernel Runtime Engine.

Orchestrates local capability vaults, Nash bargaining coordination,
atomic capability escrow, and dynamic peer market clearing.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple

from pactum.bargaining.nash import NashBargainingSolver
from pactum.bargaining.negotiation import NegotiationCoordinator
from pactum.core.config import PactumConfig
from pactum.core.exceptions import (
    BargainingError,
    InsufficientCapabilityError,
    LeaseExpiredError,
    PactumError,
)
from pactum.core.types import (
    AtomicLease,
    BargainingAgreement,
    BarterOffer,
    CapabilityToken,
    ResourceType,
    UtilityProfile,
)
from pactum.escrow.atomic_swap import AtomicCapabilityEscrow
from pactum.escrow.proxy import CapabilityProxy
from pactum.market.clearing_house import ClearingHouse
from pactum.market.equilibrium import EquilibriumTracker, MarketEquilibriumState
from pactum.market.peer_registry import PeerRegistry, PeerService
from pactum.resources.capability import CapabilityVault
from pactum.resources.quota import QuotaTracker
from pactum.resources.utility import UtilityBuilder

logger = logging.getLogger("pactum.kernel")


class PactumKernel:
    """
    Decentralized Coasian Capability Barter Kernel.
    """

    def __init__(self, service_id: str, config: Optional[PactumConfig] = None):
        self.service_id = service_id
        self.config = config or PactumConfig()

        # Core Subsystems
        self.vault = CapabilityVault(service_id=self.service_id, secret_key=self.config.hmac_secret_key)
        self.quota_tracker = QuotaTracker()
        self.escrow = AtomicCapabilityEscrow(
            secret_key=self.config.hmac_secret_key,
            quota_tracker=self.quota_tracker,
        )
        self.proxy = CapabilityProxy(quota_tracker=self.quota_tracker)
        self.solver = NashBargainingSolver(
            tolerance=self.config.nash_convergence_tolerance,
            max_iterations=self.config.max_bargaining_iterations,
        )
        self.coordinator = NegotiationCoordinator(solver=self.solver)
        self.peer_registry = PeerRegistry()
        self.equilibrium_tracker = EquilibriumTracker()
        self.clearing_house = ClearingHouse(
            coordinator=self.coordinator,
            escrow=self.escrow,
            peer_registry=self.peer_registry,
            equilibrium_tracker=self.equilibrium_tracker,
        )

        # Register self in peer registry
        self.peer_registry.register_peer(
            service_id=self.service_id,
            service_name=f"Service-{self.service_id}",
        )

    def mint_capability(
        self,
        resource_type: ResourceType,
        quantity: float,
        ttl_seconds: Optional[float] = None,
    ) -> CapabilityToken:
        """Mints a local capability asset into the service vault."""
        ttl = ttl_seconds or self.config.default_lease_ttl_seconds
        token = self.vault.mint_capability(
            resource_type=resource_type,
            quantity=quantity,
            ttl_seconds=ttl,
        )
        peer = self.peer_registry.get_peer(self.service_id)
        if peer:
            peer.owned_capabilities.add(resource_type)
        return token

    def propose_barter(
        self,
        offered_type: ResourceType,
        offered_quantity: float,
        requested_type: ResourceType,
        min_requested_quantity: float,
        utility_profile: UtilityProfile,
        ttl_seconds: float = 60.0,
    ) -> BarterOffer:
        """Creates and submits a barter offer into the market clearing house."""
        avail = self.vault.get_available_quantity(offered_type)
        if avail < offered_quantity:
            raise InsufficientCapabilityError(
                f"Cannot propose offer of {offered_quantity} {offered_type.value}; only {avail:.2f} available."
            )

        offer = BarterOffer(
            offer_id=f"off-{uuid.uuid4().hex[:12]}",
            proposer_service_id=self.service_id,
            offered_resource_type=offered_type,
            offered_quantity=offered_quantity,
            requested_resource_type=requested_type,
            min_requested_quantity=min_requested_quantity,
            proposer_utility_profile=utility_profile,
            ttl_seconds=ttl_seconds,
        )
        self.clearing_house.submit_offer(offer, self.vault)
        return offer

    def execute_bilateral_barter(
        self,
        peer_kernel: PactumKernel,
        my_offer_type: ResourceType,
        my_offer_qty: float,
        my_requested_type: ResourceType,
        my_utility: UtilityProfile,
        peer_utility: UtilityProfile,
    ) -> Tuple[BargainingAgreement, AtomicLease, AtomicLease]:
        """
        Executes immediate bilateral barter negotiation between self and a peer kernel.
        Returns: (BargainingAgreement, MyAcquiredLease, PeerAcquiredLease)
        """
        offer_a = BarterOffer(
            offer_id=f"off-{uuid.uuid4().hex[:12]}",
            proposer_service_id=self.service_id,
            offered_resource_type=my_offer_type,
            offered_quantity=my_offer_qty,
            requested_resource_type=my_requested_type,
            min_requested_quantity=0.1,
            proposer_utility_profile=my_utility,
        )

        peer_avail = peer_kernel.vault.get_available_quantity(my_requested_type)
        offer_b = BarterOffer(
            offer_id=f"off-{uuid.uuid4().hex[:12]}",
            proposer_service_id=peer_kernel.service_id,
            offered_resource_type=my_requested_type,
            offered_quantity=peer_avail,
            requested_resource_type=my_offer_type,
            min_requested_quantity=0.1,
            proposer_utility_profile=peer_utility,
        )

        agreement = self.coordinator.negotiate(
            offer_a=offer_a,
            offer_b=offer_b,
            vault_a=self.vault,
            vault_b=peer_kernel.vault,
        )

        lease_a, lease_b = self.escrow.execute_atomic_swap(
            agreement=agreement,
            vault_a=self.vault,
            vault_b=peer_kernel.vault,
            ttl_seconds=self.config.default_lease_ttl_seconds,
        )

        self.equilibrium_tracker.record_agreement(agreement)
        peer_kernel.equilibrium_tracker.record_agreement(agreement)

        return agreement, lease_b, lease_a

    def execute_with_leased_capability(
        self,
        lease_id: str,
        operation: Callable[..., Any],
        cost: float = 1.0,
        *args,
        **kwargs,
    ) -> Any:
        """Executes a function protected by leased bartered capacity."""
        success, result, _ = self.proxy.execute_with_lease(
            lease_id=lease_id,
            operation_callable=operation,
            cost_amount=cost,
            *args,
            **kwargs,
        )
        return result

    def get_market_state(self) -> MarketEquilibriumState:
        return self.equilibrium_tracker.get_equilibrium_snapshot()
