"""
Sliding-Window Quota Tracking and Consumption Rate Limiting for Leased Capabilities.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Dict, Optional, Tuple

from pactum.core.exceptions import LeaseExpiredError, LeaseQuotaExceededError
from pactum.core.types import AtomicLease, LeaseStatus


class QuotaTracker:
    """
    Thread-Safe High-Precision Consumption Rate Tracker for Leased Capability Tokens.
    """

    def __init__(self):
        self._leases: Dict[str, AtomicLease] = {}
        self._consumption_history: Dict[str, deque] = {}
        self._lock = threading.RLock()

    def register_lease(self, lease: AtomicLease) -> None:
        with self._lock:
            self._leases[lease.lease_id] = lease
            self._consumption_history[lease.lease_id] = deque()

    def consume(self, lease_id: str, amount: float = 1.0) -> Tuple[bool, float, float]:
        """
        Consumes `amount` from the active lease.
        Returns: (success: bool, remaining_capacity: float, consumed_total: float)
        Raises LeaseExpiredError or LeaseQuotaExceededError on violation.
        """
        now = time.time()
        with self._lock:
            lease = self._leases.get(lease_id)
            if not lease:
                raise LeaseExpiredError(f"Lease '{lease_id}' not found in quota tracker.")

            if not lease.is_valid(now):
                if now >= lease.expires_at:
                    lease.status = LeaseStatus.EXPIRED
                    raise LeaseExpiredError(f"Lease '{lease_id}' expired at {lease.expires_at}.")
                raise LeaseQuotaExceededError(
                    f"Lease '{lease_id}' exhausted. Allocated: {lease.allocated_quantity}, "
                    f"Consumed: {lease.consumed_quantity}."
                )

            if lease.consumed_quantity + amount > lease.allocated_quantity:
                remaining = max(0.0, lease.allocated_quantity - lease.consumed_quantity)
                raise LeaseQuotaExceededError(
                    f"Requested {amount:.2f} exceeds remaining lease capacity {remaining:.2f}."
                )

            lease.consumed_quantity += amount
            self._consumption_history[lease_id].append((now, amount))

            remaining = lease.allocated_quantity - lease.consumed_quantity
            if remaining <= 0:
                lease.status = LeaseStatus.CONSUMED

            return True, remaining, lease.consumed_quantity

    def get_lease(self, lease_id: str) -> Optional[AtomicLease]:
        with self._lock:
            return self._leases.get(lease_id)
