"""
Integration tests for End-to-End Rate Limit Barter Flow between two autonomous microservices.
"""

import pytest
from pactum.core.types import ResourceType
from pactum.engine.kernel import PactumKernel
from pactum.resources.utility import UtilityBuilder


def test_end_to_end_rate_limit_barter(kernel_a, kernel_b):
    # Service A (e.g. Auth) has surplus OpenAI API rate limit, needs Stripe API tokens
    kernel_a.mint_capability(ResourceType.API_RATE_LIMIT, 1000.0)

    # Service B (e.g. Billing) has surplus Stripe API tokens, needs OpenAI API rate limit
    kernel_b.mint_capability(ResourceType.API_RATE_LIMIT, 500.0)

    u_a = UtilityBuilder.rate_limit_urgency(current_deficit_rate=150.0)
    u_b = UtilityBuilder.rate_limit_urgency(current_deficit_rate=200.0)

    # Execute bilateral barter
    agreement, lease_a, lease_b = kernel_a.execute_bilateral_barter(
        peer_kernel=kernel_b,
        my_offer_type=ResourceType.API_RATE_LIMIT,
        my_offer_qty=1000.0,
        my_requested_type=ResourceType.API_RATE_LIMIT,
        my_utility=u_a,
        peer_utility=u_b,
    )

    assert agreement.is_pareto_optimal is True
    assert agreement.quantity_a_to_b > 0
    assert agreement.quantity_b_to_a > 0

    # Service A executes task with leased capability
    def call_stripe():
        return "Stripe Charge 200 OK"

    res = kernel_a.execute_with_leased_capability(lease_a.lease_id, call_stripe, cost=1.0)
    assert res == "Stripe Charge 200 OK"
