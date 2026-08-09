"""
Pytest fixtures and configuration for Pactum test suite.
"""

import pytest
from pactum.core.config import PactumConfig
from pactum.engine.kernel import PactumKernel


@pytest.fixture
def secret_key():
    return "test-pactum-secret-key-32bytes-long-super-secure!"


@pytest.fixture
def test_config(secret_key):
    return PactumConfig(
        environment="test",
        hmac_secret_key=secret_key,
        default_lease_ttl_seconds=120.0,
    )


@pytest.fixture
def kernel_a(test_config):
    return PactumKernel("service-alpha", config=test_config)


@pytest.fixture
def kernel_b(test_config):
    return PactumKernel("service-beta", config=test_config)
