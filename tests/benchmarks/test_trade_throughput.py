"""
End-to-End Barter Swap Throughput Benchmark.
"""

import time
import pytest
from pactum.core.types import ResourceType
from pactum.engine.kernel import PactumKernel
from pactum.resources.utility import UtilityBuilder


def test_end_to_end_barter_settlement_throughput(test_config):
    kernel_a = PactumKernel("perf-a", config=test_config)
    kernel_b = PactumKernel("perf-b", config=test_config)

    kernel_a.mint_capability(ResourceType.API_RATE_LIMIT, 50000.0)
    kernel_b.mint_capability(ResourceType.GPU_VRAM_MB_SEC, 500000.0)

    u_a = UtilityBuilder.rate_limit_urgency(100.0)
    u_b = UtilityBuilder.idle_capacity_surplus(500000.0)

    iterations = 200
    start = time.perf_counter()
    for _ in range(iterations):
        agreement, lease_a, lease_b = kernel_a.execute_bilateral_barter(
            peer_kernel=kernel_b,
            my_offer_type=ResourceType.API_RATE_LIMIT,
            my_offer_qty=10.0,
            my_requested_type=ResourceType.GPU_VRAM_MB_SEC,
            my_utility=u_a,
            peer_utility=u_b,
        )
        assert lease_a.is_valid()
        assert lease_b.is_valid()
    total_time_s = time.perf_counter() - start

    ops_sec = iterations / total_time_s
    print(f"\n[BENCHMARK] Full End-to-End Barter Settlement Throughput: {ops_sec:,.1f} trades/sec")
    assert ops_sec > 100.0
