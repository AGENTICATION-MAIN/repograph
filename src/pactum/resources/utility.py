"""
Utility Function Builders and Marginal Value Profiles for Pactum.
"""

from __future__ import annotations

import math
from typing import Optional

from pactum.core.types import UtilityFunctionType, UtilityProfile


class UtilityBuilder:
    """
    Factory for constructing standardized economic utility profiles based on engineering SLA constraints.
    """

    @staticmethod
    def rate_limit_urgency(
        current_deficit_rate: float,
        critical_threshold: float = 100.0,
        disagreement_penalty: float = -10.0,
    ) -> UtilityProfile:
        """
        Creates a logarithmic diminishing-returns utility profile for API rate limit requests.
        Higher deficit generates higher alpha (urgency scaling).
        """
        # alpha scaled with deficit severity
        alpha = max(1.0, current_deficit_rate / 10.0)
        beta = 0.05
        return UtilityProfile(
            function_type=UtilityFunctionType.CONCAVE_LOGARITHMIC,
            alpha=alpha,
            beta=beta,
            reservation_utility=disagreement_penalty,
            max_capacity_needed=critical_threshold * 1.5,
        )

    @staticmethod
    def idle_capacity_surplus(
        available_surplus: float,
        opportunity_cost_weight: float = 0.1,
    ) -> UtilityProfile:
        """
        Creates a low-alpha linear profile representing a service willing to trade away idle capacity.
        """
        return UtilityProfile(
            function_type=UtilityFunctionType.PIECEWISE_LINEAR,
            alpha=opportunity_cost_weight,
            beta=0.01,
            reservation_utility=0.0,
            max_capacity_needed=available_surplus,
        )

    @staticmethod
    def priority_queue_urgency(
        p99_latency_sla_ms: float,
        current_queue_depth: int,
    ) -> UtilityProfile:
        """
        Creates an exponential urgency profile for high-priority queue slot requirements.
        """
        urgency_multiplier = math.log(1 + current_queue_depth) * (1000.0 / max(10.0, p99_latency_sla_ms))
        return UtilityProfile(
            function_type=UtilityFunctionType.EXPONENTIAL_URGENCY,
            alpha=urgency_multiplier,
            beta=0.2,
            reservation_utility=-20.0,
            max_capacity_needed=50.0,
        )
