# Pactum REST API Reference

## Base URL
`http://localhost:8000/api/v1`

## Endpoints

### 1. Mint Local Capability Tokens
- **POST** `/api/v1/capabilities/mint`
- **Request Body**:
  ```json
  {
    "resource_type": "API_RATE_LIMIT",
    "quantity": 500.0,
    "ttl_seconds": 300.0
  }
  ```

### 2. Submit Barter Offer to Clearing House
- **POST** `/api/v1/offers`
- **Request Body**:
  ```json
  {
    "offered_resource_type": "API_RATE_LIMIT",
    "offered_quantity": 200.0,
    "requested_resource_type": "GPU_VRAM_MB_SEC",
    "min_requested_quantity": 1000.0,
    "utility_alpha": 2.5
  }
  ```

### 3. Trigger Autonomous Market Clearing
- **POST** `/api/v1/market/clear`
- **Response**: Returns list of cleared bilateral trades, agreements, and atomic leases.

### 4. Consume Units from Leased Capability
- **POST** `/api/v1/leases/consume`
- **Request Body**:
  ```json
  {
    "lease_id": "lease-abc12345",
    "amount": 1.0
  }
  ```

### 5. Market Equilibrium Snapshot
- **GET** `/api/v1/market/equilibrium`
- Returns current empirical shadow exchange rates and total social welfare gained.
