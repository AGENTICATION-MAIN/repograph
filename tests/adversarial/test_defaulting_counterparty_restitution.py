"""
Adversarial Tests: Counterparty Default Restitution & Two-Phase Rollback.
"""

import pytest
from pactum.core.exceptions import EscrowSettlementError
from pactum.core.types import BargainingAgreement, ResourceType
from pactum.escrow.atomic_swap import AtomicCapabilityEscrow
from pactum.resources.capability import CapabilityVault
from pactum.resources.quota import QuotaTracker


def test_escrow_atomic_rollback_on_counterparty_shortfall(secret_key):
    quota_tracker = QuotaTracker()
    escrow = AtomicCapabilityEscrow(secret_key, quota_tracker)

    vault_a = CapabilityVault("service-a", secret_key)
    vault_b = CapabilityVault("service-b", secret_key)

    # Party A has enough (500), but Party B has 0!
    vault_a.mint_capability(ResourceType.API_RATE_LIMIT, 500.0)

    agreement = BargainingAgreement(
        agreement_id="agr-default",
        party_a_id="service-a",
        party_b_id="service-b",
        resource_a_to_b_type=ResourceType.API_RATE_LIMIT,
        quantity_a_to_b=100.0,
        resource_b_to_a_type=ResourceType.GPU_VRAM_MB_SEC,
        quantity_b_to_a=500.0,
        nash_product=10.0,
        surplus_utility_a=1.0,
        surplus_utility_b=1.0,
        is_pareto_optimal=True,
        solving_latency_us=100.0,
    )

    with pytest.raises(EscrowSettlementError):
        escrow.execute_atomic_swap(agreement, vault_a, vault_b)

    # Party A's reservation must be completely restored
    assert vault_a.get_available_quantity(ResourceType.API_RATE_LIMIT) == 500.0
