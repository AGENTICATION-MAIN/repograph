#!/usr/bin/env python3
"""
04_dynamic_equilibrium_market.py — Multi-Agent Clearing House & Shadow Price Discovery.
"""

from pactum import PactumKernel, ResourceType, UtilityBuilder

def main():
    print("=== Pactum: Autonomous Multi-Party Clearing House & Price Discovery ===")

    # Initialize a market network with 4 specialized services
    hub = PactumKernel("clearing-hub")
    
    service_a = PactumKernel("service-A")
    service_b = PactumKernel("service-B")
    service_c = PactumKernel("service-C")
    service_d = PactumKernel("service-D")

    # Mint resources across services
    service_a.mint_capability(ResourceType.API_RATE_LIMIT, 500.0)
    service_b.mint_capability(ResourceType.GPU_VRAM_MB_SEC, 8192.0)
    service_c.mint_capability(ResourceType.QUEUE_PRIORITY_SLOT, 100.0)
    service_d.mint_capability(ResourceType.API_RATE_LIMIT, 300.0)

    # Submit complementary barter offers to the clearing house
    hub.clearing_house.submit_offer(
        service_a.propose_barter(
            offered_type=ResourceType.API_RATE_LIMIT,
            offered_quantity=200.0,
            requested_type=ResourceType.GPU_VRAM_MB_SEC,
            min_requested_quantity=1000.0,
            utility_profile=UtilityBuilder.rate_limit_urgency(100.0),
        ),
        service_a.vault
    )

    hub.clearing_house.submit_offer(
        service_b.propose_barter(
            offered_type=ResourceType.GPU_VRAM_MB_SEC,
            offered_quantity=4096.0,
            requested_type=ResourceType.API_RATE_LIMIT,
            min_requested_quantity=50.0,
            utility_profile=UtilityBuilder.rate_limit_urgency(150.0),
        ),
        service_b.vault
    )

    print(f"Submitted 2 complementary offers into Clearing House.")
    print("Scanning and executing autonomous market clearing match...")

    cleared = hub.clearing_house.scan_and_clear_matches()
    print(f"✓ Cleared {len(cleared)} bilateral trades atomically.")

    eq_state = hub.get_market_state()
    print(f"\nEmergent Market Equilibrium:")
    print(f"  Total Trades Settled: {eq_state.total_trades_count}")
    print(f"  Total Social Welfare Gained: {eq_state.total_social_welfare_gained:.2f} utils")
    print(f"  Shadow Exchange Ratios: {eq_state.shadow_exchange_rates}")

if __name__ == "__main__":
    main()
