"""
Adversarial Tests: Sybil and Free-Rider Deflection.
"""

import pytest
from pactum.core.exceptions import InsufficientCapabilityError
from pactum.core.types import ResourceType
from pactum.resources.utility import UtilityBuilder


def test_free_rider_over_promising_rejection(kernel_a, kernel_b):
    # Free-rider has 0 capability tokens, tries to propose 10,000 units
    u_a = UtilityBuilder.rate_limit_urgency(100.0)

    with pytest.raises(InsufficientCapabilityError):
        kernel_a.propose_barter(
            offered_type=ResourceType.API_RATE_LIMIT,
            offered_quantity=10000.0,
            requested_type=ResourceType.GPU_VRAM_MB_SEC,
            min_requested_quantity=1.0,
            utility_profile=u_a,
        )
