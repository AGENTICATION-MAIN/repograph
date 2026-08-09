"""
Unit tests for Closed-Form Nash Bargaining Solution (NBS) and Pareto Optimality.
"""

import pytest
from pactum.bargaining.nash import NashBargainingSolver
from pactum.bargaining.pareto import ParetoValidator
from pactum.core.exceptions import NoMutuallyBeneficialTradeError
from pactum.core.types import BarterOffer, ResourceType, UtilityFunctionType, UtilityProfile


def test_nash_bargaining_solution_convergence():
    solver = NashBargainingSolver()

    u_a = UtilityProfile(function_type=UtilityFunctionType.CONCAVE_LOGARITHMIC, alpha=2.0, beta=0.1)
    u_b = UtilityProfile(function_type=UtilityFunctionType.CONCAVE_LOGARITHMIC, alpha=1.5, beta=0.1)

    offer_a = BarterOffer(
        offer_id="off-1",
        proposer_service_id="party-a",
        offered_resource_type=ResourceType.API_RATE_LIMIT,
        offered_quantity=300.0,
        requested_resource_type=ResourceType.GPU_VRAM_MB_SEC,
        min_requested_quantity=10.0,
        proposer_utility_profile=u_a,
    )

    offer_b = BarterOffer(
        offer_id="off-2",
        proposer_service_id="party-b",
        offered_resource_type=ResourceType.GPU_VRAM_MB_SEC,
        offered_quantity=4096.0,
        requested_resource_type=ResourceType.API_RATE_LIMIT,
        min_requested_quantity=10.0,
        proposer_utility_profile=u_b,
    )

    agreement = solver.solve(offer_a, offer_b, available_cap_a=300.0, available_cap_b=4096.0)

    assert agreement.quantity_a_to_b > 0
    assert agreement.quantity_b_to_a > 0
    assert agreement.nash_product > 0
    assert agreement.surplus_utility_a > 0
    assert agreement.surplus_utility_b > 0
    assert agreement.solving_latency_us < 2000.0  # Sub-2ms solving latency


def test_incompatible_resource_rejection():
    solver = NashBargainingSolver()

    u = UtilityProfile(function_type=UtilityFunctionType.PIECEWISE_LINEAR, alpha=1.0)

    offer_a = BarterOffer(
        offer_id="off-1",
        proposer_service_id="party-a",
        offered_resource_type=ResourceType.API_RATE_LIMIT,
        offered_quantity=100.0,
        requested_resource_type=ResourceType.GPU_VRAM_MB_SEC,
        min_requested_quantity=1.0,
        proposer_utility_profile=u,
    )

    # Incompatible: party B also offers API_RATE_LIMIT
    offer_b = BarterOffer(
        offer_id="off-2",
        proposer_service_id="party-b",
        offered_resource_type=ResourceType.API_RATE_LIMIT,
        offered_quantity=100.0,
        requested_resource_type=ResourceType.BURST_CPU_CREDIT,
        min_requested_quantity=1.0,
        proposer_utility_profile=u,
    )

    with pytest.raises(NoMutuallyBeneficialTradeError):
        solver.solve(offer_a, offer_b, 100.0, 100.0)
