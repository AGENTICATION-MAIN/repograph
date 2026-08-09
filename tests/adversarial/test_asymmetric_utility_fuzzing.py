"""
Adversarial Tests: Extreme Asymmetric Utility Curve Fuzzing & Numerical Stability.
"""

import pytest
from pactum.bargaining.nash import NashBargainingSolver
from pactum.core.exceptions import NoMutuallyBeneficialTradeError
from pactum.core.types import BarterOffer, ResourceType, UtilityFunctionType, UtilityProfile


@pytest.mark.parametrize("alpha_a, alpha_b, cap_a, cap_b", [
    (1e6, 0.001, 1000.0, 10.0),
    (0.01, 10000.0, 50.0, 5000.0),
    (100.0, 100.0, 0.01, 100000.0),
])
def test_nash_solver_numerical_stability_under_extreme_asymmetry(alpha_a, alpha_b, cap_a, cap_b):
    solver = NashBargainingSolver()

    u_a = UtilityProfile(function_type=UtilityFunctionType.CONCAVE_LOGARITHMIC, alpha=alpha_a, beta=0.1)
    u_b = UtilityProfile(function_type=UtilityFunctionType.CONCAVE_LOGARITHMIC, alpha=alpha_b, beta=0.1)

    offer_a = BarterOffer(
        offer_id="fuzz-a",
        proposer_service_id="a",
        offered_resource_type=ResourceType.API_RATE_LIMIT,
        offered_quantity=cap_a,
        requested_resource_type=ResourceType.GPU_VRAM_MB_SEC,
        min_requested_quantity=0.001,
        proposer_utility_profile=u_a,
    )

    offer_b = BarterOffer(
        offer_id="fuzz-b",
        proposer_service_id="b",
        offered_resource_type=ResourceType.GPU_VRAM_MB_SEC,
        offered_quantity=cap_b,
        requested_resource_type=ResourceType.API_RATE_LIMIT,
        min_requested_quantity=0.001,
        proposer_utility_profile=u_b,
    )

    # Must never crash with NaN, Inf, or ZeroDivision
    try:
        agr = solver.solve(offer_a, offer_b, cap_a, cap_b)
        assert agr.quantity_a_to_b <= cap_a
        assert agr.quantity_b_to_a <= cap_b
    except NoMutuallyBeneficialTradeError:
        pass
