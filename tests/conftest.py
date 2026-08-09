"""
Pytest configuration and shared fixtures for AegisKernel test suite.
"""

import pytest
from aegis.core.config import AegisConfig
from aegis.core.kernel import AegisKernel
from aegis.core.types import TaintLevel


@pytest.fixture
def secret_key():
    return "test-secret-key-32bytes-long-super-secure!"


@pytest.fixture
def test_config(secret_key):
    return AegisConfig(
        environment="test",
        hmac_secret_key=secret_key,
        strict_invariants=True,
        taint_tracking_enabled=True,
        db_path=":memory:",
        default_rate_limit_per_minute=5000,
    )


@pytest.fixture
def kernel(test_config):
    return AegisKernel(test_config)
