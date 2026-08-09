"""
Adversarial Tests: Capability Lease Tampering & Signature Forgery Detection.
"""

import time
import pytest
from pactum.core.types import AtomicLease, ResourceType
from pactum.escrow.lease import compute_lease_signature, verify_lease_signature


def test_lease_signature_forgery_rejection(secret_key):
    lease = AtomicLease(
        lease_id="lease-evil-1",
        agreement_id="agr-fake",
        resource_type=ResourceType.API_RATE_LIMIT,
        granter_service_id="victim",
        grantee_service_id="attacker",
        allocated_quantity=10000.0,
        starts_at=time.time(),
        expires_at=time.time() + 3600.0,
        signature="bad-signature-deadbeef",
    )

    # Must fail cryptographic verification
    assert verify_lease_signature(lease, secret_key) is False

    # Sign correctly with real key
    lease.signature = compute_lease_signature(lease, secret_key)
    assert verify_lease_signature(lease, secret_key) is True

    # Tamper with allocated quantity
    lease.allocated_quantity = 999999.0
    assert verify_lease_signature(lease, secret_key) is False
