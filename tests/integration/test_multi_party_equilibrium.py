"""
Integration tests for Multi-Party Market Equilibrium and Price Discovery.
"""

import pytest
from pactum.core.types import ResourceType
from pactum.engine.kernel import PactumKernel
from pactum.resources.utility import UtilityBuilder


def test_clearing_house_multi_service_matching(test_config):
    hub = PactumKernel("clearing-hub", config=test_config)

    s1 = PactumKernel("s1", config=test_config)
    s2 = PactumKernel("s2", config=test_config)

    s1.mint_capability(ResourceType.API_RATE_LIMIT, 500.0)
    s2.mint_capability(ResourceType.GPU_VRAM_MB_SEC, 4096.0)

    # Submit complementary offers
    hub.clearing_house.submit_offer(
        s1.propose_barter(
            offered_type=ResourceType.API_RATE_LIMIT,
            offered_quantity=250.0,
            requested_type=ResourceType.GPU_VRAM_MB_SEC,
            min_requested_quantity=100.0,
            utility_profile=UtilityBuilder.rate_limit_urgency(100.0),
        ),
        s1.vault,
    )

    hub.clearing_house.submit_offer(
        s2.propose_barter(
            offered_type=ResourceType.GPU_VRAM_MB_SEC,
            offered_quantity=2048.0,
            requested_type=ResourceType.API_RATE_LIMIT,
            min_requested_quantity=50.0,
            utility_profile=UtilityBuilder.rate_limit_urgency(150.0),
        ),
        s2.vault,
    )

    # Match and clear
    cleared = hub.clearing_house.scan_and_clear_matches()
    assert len(cleared) == 1

    eq = hub.get_market_state()
    assert eq.total_trades_count == 1
    assert eq.total_social_welfare_gained > 0
