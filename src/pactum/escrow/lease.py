"""
Atomic Capability Lease Lifecycle & Signature Management for Pactum.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from typing import Optional

from pactum.core.types import AtomicLease, LeaseStatus, ResourceType


def compute_lease_signature(lease: AtomicLease, secret_key: str) -> str:
    """Generates cryptographic HMAC-SHA256 signature for an atomic capability lease."""
    canonical = {
        "lease_id": lease.lease_id,
        "agreement_id": lease.agreement_id,
        "resource_type": lease.resource_type.value,
        "granter_service_id": lease.granter_service_id,
        "grantee_service_id": lease.grantee_service_id,
        "allocated_quantity": lease.allocated_quantity,
        "starts_at": round(lease.starts_at, 4),
        "expires_at": round(lease.expires_at, 4),
    }
    raw = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(secret_key.encode("utf-8"), raw, hashlib.sha256).hexdigest()


def verify_lease_signature(lease: AtomicLease, secret_key: str) -> bool:
    """Verifies timing-safe cryptographic signature on lease."""
    expected = compute_lease_signature(lease, secret_key)
    return hmac.compare_digest(lease.signature, expected)
