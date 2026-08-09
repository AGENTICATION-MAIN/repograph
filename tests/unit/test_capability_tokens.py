"""
Unit tests for Capability Vault and Token signing.
"""

import pytest
from pactum.core.types import ResourceType
from pactum.resources.capability import CapabilityVault, compute_token_signature


def test_capability_vault_minting_and_signing(secret_key):
    vault = CapabilityVault("service-x", secret_key=secret_key)
    token = vault.mint_capability(ResourceType.API_RATE_LIMIT, 500.0)

    assert token.owner_service_id == "service-x"
    assert token.total_quantity == 500.0
    assert token.signature != ""

    # Verify signature
    expected_sig = compute_token_signature(token, secret_key)
    assert token.signature == expected_sig
