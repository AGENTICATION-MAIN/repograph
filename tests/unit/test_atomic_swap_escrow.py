"""
Unit tests for Atomic Capability Handover Escrow (ACHE).
"""

import pytest
from pactum.core.exceptions import EscrowSettlementError
from pactum.core.types import BargainingAgreement, ResourceType
from pactum.escrow.atomic_swap import AtomicCapabilityEscrow
from pactum.resources.capability import CapabilityVault
from pactum.resources.quota import QuotaTracker


def test_atomic_swap_execution(secret_key):
    quota_tracker = QuotaTracker()
    escrow = AtomicCapabilityEscrow(secret_key=secret_key, quota_tracker=quota_tracker)

    vault_a = CapabilityVault("service-a", secret_key=secret_key)
    vault_b = CapabilityVault("service-b", secret_key=secret_key)

    vault_a.mint_capability(ResourceType.API_RATE_LIMIT, 500.0)
    vault_b.mint_capability(ResourceType.GPU_VRAM_MB_SEC, 2048.0)

    agreement = BargainingAgreement(
        agreement_id="agr-123",
        party_a_id="service-a",
        party_b_id="service-b",
        resource_a_to_b_type=ResourceType.API_RATE_LIMIT,
        quantity_a_to_b=150.0,
        resource_b_to_a_type=ResourceType.GPU_VRAM_MB_SEC,
        quantity_b_to_a=1024.0,
        nash_product=10.5,
        surplus_utility_a=3.2,
        surplus_utility_b=3.3,
        is_pareto_optimal=True,
        solving_latency_us=120.0,
    )

    lease_a, lease_b = escrow.execute_atomic_swap(agreement, vault_a, vault_b)

    assert lease_a.allocated_quantity == 150.0
    assert lease_b.allocated_quantity == 1024.0
    assert vault_a.get_available_quantity(ResourceType.API_RATE_LIMIT) == 350.0
    assert vault_b.get_available_quantity(ResourceType.GPU_VRAM_MB_SEC) == 1024.0
