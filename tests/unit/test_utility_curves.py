"""
Unit tests for Marginal Utility Profiles and Curvature Functions.
"""

import math
import pytest
from pactum.core.types import UtilityFunctionType, UtilityProfile
from pactum.resources.utility import UtilityBuilder


def test_logarithmic_utility_diminishing_returns():
    u = UtilityProfile(
        function_type=UtilityFunctionType.CONCAVE_LOGARITHMIC,
        alpha=2.0,
        beta=0.1,
    )

    # Monotonically increasing
    u0 = u.evaluate(0.0)
    u10 = u.evaluate(10.0)
    u50 = u.evaluate(50.0)
    u100 = u.evaluate(100.0)

    assert u0 == 0.0
    assert u10 > u0
    assert u50 > u10
    assert u100 > u50

    # Diminishing marginal returns: ΔU(0 -> 10) > ΔU(90 -> 100)
    delta_initial = u.marginal_utility(0.0, 10.0)
    delta_late = u.marginal_utility(90.0, 10.0)
    assert delta_initial > delta_late


def test_utility_builder_presets():
    u_rate = UtilityBuilder.rate_limit_urgency(current_deficit_rate=150.0)
    assert u_rate.function_type == UtilityFunctionType.CONCAVE_LOGARITHMIC
    assert u_rate.alpha > 1.0

    u_queue = UtilityBuilder.priority_queue_urgency(p99_latency_sla_ms=25.0, current_queue_depth=10)
    assert u_queue.function_type == UtilityFunctionType.EXPONENTIAL_URGENCY
    assert u_queue.reservation_utility < 0.0
