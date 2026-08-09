# Atomic Capability Handover Escrow (ACHE) Protocol

The ACHE protocol executes the two-phase atomic exchange of capability assets between trading peers without requiring a trusted centralized bank.

```
Service A (Vault A)              Escrow Engine              Service B (Vault B)
       │                              │                              │
       │─────── Phase 1: Lock ───────>│<─────── Phase 1: Lock ───────│
       │    (Reserve q_A tokens)      │     (Reserve q_B tokens)     │
       │                              │                              │
       │<── Phase 2: Signed Lease B ──│── Phase 2: Signed Lease A ──>│
       │   (HMAC-SHA256 Signed)       │    (HMAC-SHA256 Signed)      │
       │                              │                              │
       │─────── Phase 3: Commit ─────>│<─────── Phase 3: Commit ─────│
       │  (Deduct from Availability)  │  (Deduct from Availability)  │
```

## Security Invariants
1. **Atomicity**: If either vault fails to reserve its allocated capacity, all reservations are rolled back instantaneously.
2. **Cryptographic Integrity**: Leases carry HMAC-SHA256 signatures over their canonical parameters. Tampered lease parameters are rejected by the proxy with zero execution privilege granted.
3. **Automatic TTL Expiration**: When the lease expiration timestamp passes, the quota tracker marks the lease `EXPIRED` and restores residual unused quota.
