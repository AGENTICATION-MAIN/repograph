# AegisKernel REST API Reference

The AegisKernel server exposes a high-performance REST API over HTTP/JSON.

## Base URL
`http://localhost:8000/api/v1`

## Endpoints

### 1. Verify Tool Execution Intent
- **Endpoint**: `POST /api/v1/verify`
- **Request Body**:
  ```json
  {
    "tool_name": "transfer_funds",
    "arguments": { "recipient": "ACC-991", "amount": 250.0 },
    "agent_id": "finance-bot",
    "session_id": "session-100",
    "capability_token_id": "cap-abc12345"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "decision": "ALLOW",
    "intent_id": "int-172323...",
    "reason": "All security and policy invariants verified.",
    "violations": [],
    "evaluation_latency_ms": 0.45,
    "merkle_node_hash": "a8f9c1...",
    "merkle_root_hash": "e3b0c4..."
  }
  ```

### 2. Mint Capability Token
- **Endpoint**: `POST /api/v1/capabilities/mint`
- **Request Body**:
  ```json
  {
    "subject_agent_id": "agent-01",
    "session_id": "session-01",
    "allowed_tools": ["query_db", "fetch_url"],
    "max_invocations": 10,
    "ttl_seconds": 3600
  }
  ```

### 3. Merkle Ledger & Cryptographic Proofs
- **Get Ledger**: `GET /api/v1/ledger?limit=50&offset=0`
- **Generate Inclusion Proof**: `GET /api/v1/ledger/proof/{intent_id}`
- **Verify Proof**: `POST /api/v1/ledger/verify-proof`

### 4. Health & Telemetry
- **Health Check**: `GET /api/v1/health`
- **Telemetry Metrics**: `GET /api/v1/metrics`
