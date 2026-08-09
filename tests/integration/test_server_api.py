"""
Integration tests for FastAPI REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from aegis.server.app import create_app


@pytest.fixture
def client(kernel, test_config):
    app = create_app(kernel=kernel, config=test_config)
    return TestClient(app)


def test_api_health(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["ledger_integrity"] is True


def test_api_verify_intent(client):
    payload = {
        "tool_name": "transfer_funds",
        "arguments": {"amount": 250.0, "recipient": "vendor-1"},
        "agent_id": "api-agent",
        "session_id": "api-session",
    }
    res = client.post("/api/v1/verify", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "ALLOW"
    assert "merkle_node_hash" in data


def test_api_capability_mint_and_list(client):
    req = {
        "subject_agent_id": "test-agent",
        "session_id": "test-session",
        "allowed_tools": ["read_data", "write_data"],
        "max_invocations": 10,
        "ttl_seconds": 1800,
    }
    res = client.post("/api/v1/capabilities/mint", json=req)
    assert res.status_code == 200
    token_data = res.json()
    assert token_data["token_id"].startswith("cap-")

    list_res = client.get("/api/v1/capabilities")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_api_policy_crud(client):
    rule_req = {
        "rule_id": "API_TEST_RULE",
        "rule_name": "API Test Rule",
        "description": "Rule created via REST API",
        "phase": "PRE_EXECUTION",
        "condition": {"field": "args.val", "op": ">=", "value": 0},
        "target_tools": ["test_tool"],
    }
    res = client.post("/api/v1/policies", json=rule_req)
    assert res.status_code == 200

    list_res = client.get("/api/v1/policies")
    assert any(r["rule_id"] == "API_TEST_RULE" for r in list_res.json())

    del_res = client.delete("/api/v1/policies/API_TEST_RULE")
    assert del_res.status_code == 200


def test_api_merkle_ledger_and_proof(client):
    # Execute an intent to ensure at least 1 record
    client.post("/api/v1/verify", json={
        "tool_name": "log_event",
        "arguments": {"msg": "hello"},
        "agent_id": "agent-log",
        "session_id": "session-log",
        "intent_id": "intent-fixed-123",
    })

    ledger_res = client.get("/api/v1/ledger")
    assert ledger_res.status_code == 200
    ledger_data = ledger_res.json()
    assert ledger_data["total_records"] >= 1

    proof_res = client.get("/api/v1/ledger/proof/intent-fixed-123")
    assert proof_res.status_code == 200
    proof_data = proof_res.json()
    assert proof_data["leaf_hash"] != ""

    # Verify proof via API
    ver_res = client.post("/api/v1/ledger/verify-proof", json=proof_data)
    assert ver_res.status_code == 200
    assert ver_res.json()["verified"] is True
