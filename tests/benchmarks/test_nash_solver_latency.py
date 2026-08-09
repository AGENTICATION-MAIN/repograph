"""
Performance & Microsecond Latency Benchmarks for Pactum Nash Bargaining Solver.
"""

import time
import pytest
from pactum.bargaining.nash import NashBargainingSolver
from pactum.core.types import BarterOffer, ResourceType, UtilityFunctionType, UtilityProfile


def test_nash_solver_submillisecond_latency():
    solver = NashBargainingSolver()

    u_a = UtilityProfile(function_type=UtilityFunctionType.CONCAVE_LOGARITHMIC, alpha=2.0, beta=0.1)
    u_b = UtilityProfile(function_type=UtilityFunctionType.CONCAVE_LOGARITHMIC, alpha=1.8, beta=0.1)

    offer_a = BarterOffer(
        offer_id="bench-a",
        proposer_service_id="svc-a",
        offered_resource_type=ResourceType.API_RATE_LIMIT,
        offered_quantity=500.0,
        requested_resource_type=ResourceType.GPU_VRAM_MB_SEC,
        min_requested_quantity=10.0,
        proposer_utility_profile=u_a,
    )

    offer_b = BarterOffer(
        offer_id="bench-b",
        proposer_service_id="svc-b",
        offered_resource_type=ResourceType.GPU_VRAM_MB_SEC,
        offered_quantity=4096.0,
        requested_resource_type=ResourceType.API_RATE_LIMIT,
        min_requested_quantity=10.0,
        proposer_utility_profile=u_b,
    )

    # Warmup
    for _ in range(20):
        solver.solve(offer_a, offer_b, 500.0, 4096.0)

    # Measure 500 iterations
    iterations = 500
    start = time.perf_counter()
    for _ in range(iterations):
        agr = solver.solve(offer_a, offer_b, 500.0, 4096.0)
        assert agr.nash_product > 0
    total_time_s = time.perf_counter() - start

    avg_latency_us = (total_time_s / iterations) * 1_000_000.0
    throughput = iterations / total_time_s

    print(f"\n[BENCHMARK] Avg Nash Solver Latency: {avg_latency_us:.1f} μs | Throughput: {throughput:,.1f} trades/sec")

    # Assert sub-millisecond solving latency (<1000 μs)
    assert avg_latency_us < 1000.0, f"Latency exceeded sub-millisecond target: {avg_latency_us:.1f} μs"
