"""
Integration tests for Priority Queue & GPU VRAM cross-resource barter exchange.
"""

import pytest
from pactum.core.types import ResourceType
from pactum.resources.utility import UtilityBuilder


def test_queue_priority_for_gpu_vram_swap(kernel_a, kernel_b):
    kernel_a.mint_capability(ResourceType.QUEUE_PRIORITY_SLOT, 100.0)
    kernel_b.mint_capability(ResourceType.GPU_VRAM_MB_SEC, 8192.0)

    u_a = UtilityBuilder.rate_limit_urgency(100.0)
    u_b = UtilityBuilder.priority_queue_urgency(p99_latency_sla_ms=30.0, current_queue_depth=15)

    agreement, lease_a, lease_b = kernel_a.execute_bilateral_barter(
        peer_kernel=kernel_b,
        my_offer_type=ResourceType.QUEUE_PRIORITY_SLOT,
        my_offer_qty=100.0,
        my_requested_type=ResourceType.GPU_VRAM_MB_SEC,
        my_utility=u_a,
        peer_utility=u_b,
    )

    assert agreement.is_pareto_optimal is True
    assert agreement.quantity_a_to_b > 0
    assert agreement.quantity_b_to_a > 0
