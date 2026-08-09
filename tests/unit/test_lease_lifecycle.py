"""
Unit tests for Atomic Lease consumption, expiration, and quota enforcement.
"""

import time
import pytest
from pactum.core.exceptions import LeaseExpiredError, LeaseQuotaExceededError
from pactum.core.types import AtomicLease, LeaseStatus, ResourceType
from pactum.resources.quota import QuotaTracker


def test_lease_consumption_and_exhaustion():
    tracker = QuotaTracker()

    lease = AtomicLease(
        lease_id="lease-test-1",
        agreement_id="agr-1",
        resource_type=ResourceType.API_RATE_LIMIT,
        granter_service_id="service-a",
        grantee_service_id="service-b",
        allocated_quantity=10.0,
        starts_at=time.time(),
        expires_at=time.time() + 60.0,
    )
    tracker.register_lease(lease)

    # Consume 4 units
    ok, remaining, total = tracker.consume(lease.lease_id, 4.0)
    assert ok is True
    assert remaining == 6.0
    assert total == 4.0

    # Consume 6 units (exhausts lease)
    ok2, remaining2, total2 = tracker.consume(lease.lease_id, 6.0)
    assert remaining2 == 0.0
    assert lease.status == LeaseStatus.CONSUMED

    # Attempt to consume past quota
    with pytest.raises(LeaseQuotaExceededError):
        tracker.consume(lease.lease_id, 1.0)
