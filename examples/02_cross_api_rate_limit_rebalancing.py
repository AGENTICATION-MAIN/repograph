#!/usr/bin/env python3
"""
02_cross_api_rate_limit_rebalancing.py — Rebalancing Asymmetric Third-Party API Quotas between Services.
"""

from pactum import PactumKernel, ResourceType, UtilityBuilder

def main():
    print("=== Pactum: Cross-API Rate Limit Barter Rebalancing ===")

    # Service 1: Payment Checkout (Needs Stripe Rate Limit, Has excess Twilio SMS capacity)
    checkout = PactumKernel("checkout-service")
    checkout.mint_capability(ResourceType.API_RATE_LIMIT, quantity=1000.0, ttl_seconds=300)

    # Service 2: Notification Service (Has excess Stripe Rate Limit, Starved on Twilio SMS capacity)
    notifier = PactumKernel("notification-service")
    notifier.mint_capability(ResourceType.BURST_CPU_CREDIT, quantity=400.0, ttl_seconds=300)

    u_checkout = UtilityBuilder.rate_limit_urgency(current_deficit_rate=250.0)
    u_notifier = UtilityBuilder.rate_limit_urgency(current_deficit_rate=180.0)

    agreement, lease_checkout, lease_notifier = checkout.execute_bilateral_barter(
        peer_kernel=notifier,
        my_offer_type=ResourceType.API_RATE_LIMIT,
        my_offer_qty=1000.0,
        my_requested_type=ResourceType.BURST_CPU_CREDIT,
        my_utility=u_checkout,
        peer_utility=u_notifier,
    )

    print(f"✓ Rebalanced API resources between checkout and notifier services:")
    print(f"  Checkout transferred: {agreement.quantity_a_to_b:.1f} API tokens")
    print(f"  Notifier transferred: {agreement.quantity_b_to_a:.1f} CPU Burst credits")
    print(f"  Trade verified Pareto-optimal: {agreement.is_pareto_optimal}")

if __name__ == "__main__":
    main()
