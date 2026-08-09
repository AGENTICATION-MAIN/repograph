"""
Atomic Capability Handover Escrow (ACHE) for Pactum.

Executes two-phase atomic settlement of bilateral capability barter agreements.
Ensures zero-risk atomicity: both services receive valid signed leases simultaneously or neither does.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from typing import Dict, Optional, Tuple

from pactum.core.exceptions import EscrowSettlementError
from pactum.core.types import (
    AtomicLease,
    BargainingAgreement,
    LeaseStatus,
)
from pactum.escrow.lease import compute_lease_signature
from pactum.resources.capability import CapabilityVault
from pactum.resources.quota import QuotaTracker

logger = logging.getLogger("pactum.escrow")


class AtomicCapabilityEscrow:
    """
    Two-Phase Atomic Capability Swap Escrow Engine.
    """

    def __init__(self, secret_key: str, quota_tracker: QuotaTracker):
        self.secret_key = secret_key
        self.quota_tracker = quota_tracker
        self._leases: Dict[str, AtomicLease] = {}
        self._lock = threading.RLock()

    def execute_atomic_swap(
        self,
        agreement: BargainingAgreement,
        vault_a: CapabilityVault,
        vault_b: CapabilityVault,
        ttl_seconds: float = 60.0,
    ) -> Tuple[AtomicLease, AtomicLease]:
        """
        Executes two-phase atomic exchange of capability assets:
        Phase 1: Reserve required quantities in both vaults.
        Phase 2: Mint, sign, and activate bilateral AtomicLease objects.
        Phase 3: Commit deductions and register into QuotaTracker.
        """
        with self._lock:
            # Phase 1: Lock reservations
            allocations_a = []
            allocations_b = []
            try:
                allocations_a = vault_a.reserve_quantity(
                    resource_type=agreement.resource_a_to_b_type,
                    requested_amount=agreement.quantity_a_to_b,
                )
                allocations_b = vault_b.reserve_quantity(
                    resource_type=agreement.resource_b_to_a_type,
                    requested_amount=agreement.quantity_b_to_a,
                )
            except Exception as e:
                # Rollback any partial reservation
                if allocations_a:
                    vault_a.release_reservation(allocations_a)
                if allocations_b:
                    vault_b.release_reservation(allocations_b)
                raise EscrowSettlementError(f"Atomic reservation lock failed: {str(e)}")

            # Phase 2: Mint atomic leases
            now = time.time()
            expires = now + ttl_seconds

            lease_a = AtomicLease(
                lease_id=f"lease-{uuid.uuid4().hex[:12]}",
                agreement_id=agreement.agreement_id,
                resource_type=agreement.resource_a_to_b_type,
                granter_service_id=agreement.party_a_id,
                grantee_service_id=agreement.party_b_id,
                allocated_quantity=agreement.quantity_a_to_b,
                starts_at=now,
                expires_at=expires,
                status=LeaseStatus.ACTIVE,
            )
            lease_a.signature = compute_lease_signature(lease_a, self.secret_key)

            lease_b = AtomicLease(
                lease_id=f"lease-{uuid.uuid4().hex[:12]}",
                agreement_id=agreement.agreement_id,
                resource_type=agreement.resource_b_to_a_type,
                granter_service_id=agreement.party_b_id,
                grantee_service_id=agreement.party_a_id,
                allocated_quantity=agreement.quantity_b_to_a,
                starts_at=now,
                expires_at=expires,
                status=LeaseStatus.ACTIVE,
            )
            lease_b.signature = compute_lease_signature(lease_b, self.secret_key)

            # Phase 3: Commit and register
            vault_a.commit_reservation_to_lease(allocations_a)
            vault_b.commit_reservation_to_lease(allocations_b)

            self.quota_tracker.register_lease(lease_a)
            self.quota_tracker.register_lease(lease_b)

            self._leases[lease_a.lease_id] = lease_a
            self._leases[lease_b.lease_id] = lease_b

            agreement.lease_a_id = lease_a.lease_id
            agreement.lease_b_id = lease_b.lease_id

            logger.info(
                f"Atomic swap completed for agreement {agreement.agreement_id}: "
                f"Lease A ({lease_a.lease_id}), Lease B ({lease_b.lease_id})"
            )

            return lease_a, lease_b

    def get_lease(self, lease_id: str) -> Optional[AtomicLease]:
        with self._lock:
            return self._leases.get(lease_id)

    def list_leases(self) -> List[AtomicLease]:
        with self._lock:
            return list(self._leases.values())
