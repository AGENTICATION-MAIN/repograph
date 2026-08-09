#!/usr/bin/env python3
"""
01_basic_two_service_barter.py — Basic Bilateral Capability Barter between Two Services.
"""

from pactum import PactumKernel, ResourceType, UtilityBuilder

def main():
    print("=== Pactum: Basic Two-Service Capability Barter ===")

    # Initialize two peer microservices
    service_a = PactumKernel("auth-service")
    service_b = PactumKernel("analytics-service")

    # Service A has idle API rate limit capacity (OpenAI tokens)
    service_a.mint_capability(ResourceType.API_RATE_LIMIT, quantity=500.0, ttl_seconds=120)

    # Service B has idle Queue Priority execution slots
    service_b.mint_capability(ResourceType.QUEUE_PRIORITY_SLOT, quantity=50.0, ttl_seconds=120)

    print("Initial Balances:")
    print(f"  auth-service available API rate limits: {service_a.vault.get_available_quantity(ResourceType.API_RATE_LIMIT)}")
    print(f"  analytics-service available Priority slots: {service_b.vault.get_available_quantity(ResourceType.QUEUE_PRIORITY_SLOT)}")

    # Define marginal utility curves
    u_a = UtilityBuilder.priority_queue_urgency(p99_latency_sla_ms=50.0, current_queue_depth=12)
    u_b = UtilityBuilder.rate_limit_urgency(current_deficit_rate=80.0)

    # Execute bilateral Nash Bargaining
    agreement, lease_a, lease_b = service_a.execute_bilateral_barter(
        peer_kernel=service_b,
        my_offer_type=ResourceType.API_RATE_LIMIT,
        my_offer_qty=500.0,
        my_requested_type=ResourceType.QUEUE_PRIORITY_SLOT,
        my_utility=u_a,
        peer_utility=u_b,
    )

    print("\n✓ Trade Ratified at Pareto Nash Equilibrium:")
    print(f"  Solving Time: {agreement.solving_latency_us:.1f} microseconds")
    print(f"  Auth Service gives: {agreement.quantity_a_to_b:.2f} API rate limit tokens")
    print(f"  Analytics Service gives: {agreement.quantity_b_to_a:.2f} Queue priority slots")
    print(f"  Social Welfare Surplus: +{agreement.surplus_utility_a + agreement.surplus_utility_b:.2f} utils")

    # Consume leased capability via proxy
    print("\nExecuting workload with newly acquired capability lease:")
    def run_priority_job():
        return "Job processed in 12ms under priority queue lease"

    res = service_a.execute_with_leased_capability(lease_a.lease_id, run_priority_job, cost=1.0)
    print(f"  Output: {res}")
    print(f"  Remaining lease quota: {service_a.quota_tracker.get_lease(lease_a.lease_id).allocated_quantity - service_a.quota_tracker.get_lease(lease_a.lease_id).consumed_quantity}")

if __name__ == "__main__":
    main()
