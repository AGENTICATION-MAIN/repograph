"""
Decentralized Clearing House & Autonomous Matching Engine for Pactum.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Dict, List, Optional, Tuple

from pactum.bargaining.negotiation import NegotiationCoordinator
from pactum.core.exceptions import NoMutuallyBeneficialTradeError
from pactum.core.types import (
    AtomicLease,
    BargainingAgreement,
    BarterOffer,
    ResourceType,
)
from pactum.escrow.atomic_swap import AtomicCapabilityEscrow
from pactum.market.equilibrium import EquilibriumTracker
from pactum.market.peer_registry import PeerRegistry
from pactum.resources.capability import CapabilityVault

logger = logging.getLogger("pactum.clearing")


class ClearingHouse:
    """
    Autonomous Offer Matching & Clearing Engine.
    Periodically scans submitted offers across the network and clears mutually beneficial trades.
    """

    def __init__(
        self,
        coordinator: NegotiationCoordinator,
        escrow: AtomicCapabilityEscrow,
        peer_registry: PeerRegistry,
        equilibrium_tracker: EquilibriumTracker,
    ):
        self.coordinator = coordinator
        self.escrow = escrow
        self.peer_registry = peer_registry
        self.equilibrium_tracker = equilibrium_tracker

        self._active_offers: Dict[str, Tuple[BarterOffer, CapabilityVault]] = {}
        self._lock = threading.RLock()

    def submit_offer(self, offer: BarterOffer, vault: CapabilityVault) -> None:
        """Registers an active trade offer into the clearing house."""
        with self._lock:
            self._active_offers[offer.offer_id] = (offer, vault)

    def cancel_offer(self, offer_id: str) -> bool:
        with self._lock:
            if offer_id in self._active_offers:
                del self._active_offers[offer_id]
                return True
            return False

    def scan_and_clear_matches(self) -> List[Tuple[BargainingAgreement, AtomicLease, AtomicLease]]:
        """
        Scans all active offers for complementary pairs, runs Nash Bargaining,
        and settles atomic capability swaps.
        """
        cleared_trades = []
        with self._lock:
            offer_ids = list(self._active_offers.keys())

            # Find matching pairs
            matched_pairs = set()
            for i in range(len(offer_ids)):
                id_a = offer_ids[i]
                if id_a in matched_pairs or id_a not in self._active_offers:
                    continue
                offer_a, vault_a = self._active_offers[id_a]

                for j in range(i + 1, len(offer_ids)):
                    id_b = offer_ids[j]
                    if id_b in matched_pairs or id_b not in self._active_offers:
                        continue
                    offer_b, vault_b = self._active_offers[id_b]

                    # Check if offers are complementary
                    if (
                        offer_a.offered_resource_type == offer_b.requested_resource_type
                        and offer_b.offered_resource_type == offer_a.requested_resource_type
                        and offer_a.proposer_service_id != offer_b.proposer_service_id
                    ):
                        try:
                            # Execute bilateral negotiation
                            agreement = self.coordinator.negotiate(
                                offer_a=offer_a,
                                offer_b=offer_b,
                                vault_a=vault_a,
                                vault_b=vault_b,
                            )

                            # Execute atomic settlement
                            lease_a, lease_b = self.escrow.execute_atomic_swap(
                                agreement=agreement,
                                vault_a=vault_a,
                                vault_b=vault_b,
                            )

                            # Record equilibrium metrics
                            self.equilibrium_tracker.record_agreement(agreement)
                            self.peer_registry.update_reputation(offer_a.proposer_service_id, 0.05)
                            self.peer_registry.update_reputation(offer_b.proposer_service_id, 0.05)

                            cleared_trades.append((agreement, lease_a, lease_b))
                            matched_pairs.add(id_a)
                            matched_pairs.add(id_b)
                            break

                        except Exception as e:
                            logger.debug(f"Pair ({id_a}, {id_b}) could not clear: {str(e)}")

            # Remove settled offers
            for settled_id in matched_pairs:
                self._active_offers.pop(settled_id, None)

        return cleared_trades

    def list_active_offers(self) -> List[BarterOffer]:
        with self._lock:
            return [offer for offer, _ in self._active_offers.values()]
