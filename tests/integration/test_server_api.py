"""
Integration tests for FastAPI REST API endpoints of Pactum Barter Kernel.
"""

import pytest
from fastapi.testclient import TestClient
from pactum.server.app import create_app


@pytest.fixture
def client(kernel_a, test_config):
    app = create_app(kernel=kernel_a, config=test_config)
    return TestClient(app)


def test_api_health(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "HEALTHY"


def test_api_mint_and_list_capabilities(client):
    req = {
        "resource_type": "API_RATE_LIMIT",
        "quantity": 300.0,
        "ttl_seconds": 180.0,
    }
    res = client.post("/api/v1/capabilities/mint", json=req)
    assert res.status_code == 200
    assert res.json()["total_quantity"] == 300.0

    list_res = client.get("/api/v1/capabilities")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_api_submit_offer(client):
    # Ensure capabilities exist
    client.post("/api/v1/capabilities/mint", json={
        "resource_type": "API_RATE_LIMIT",
        "quantity": 500.0,
    })

    offer_req = {
        "offered_resource_type": "API_RATE_LIMIT",
        "offered_quantity": 100.0,
        "requested_resource_type": "GPU_VRAM_MB_SEC",
        "min_requested_quantity": 500.0,
        "utility_alpha": 2.0,
    }
    res = client.post("/api/v1/offers", json=offer_req)
    assert res.status_code == 200
    assert res.json()["offer_id"].startswith("off-")
