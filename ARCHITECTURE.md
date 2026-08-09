# Pactum: System Architecture Specification

## 1. System Philosophy & Coasian Foundation

Pactum is a decentralized systems kernel enabling autonomous processes, microservices, and agent swarms to **barter ephemeral computing capabilities peer-to-peer** without currency or centralized coordinators.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             PACTUM BARTER MESH                              │
│                                                                             │
│  ┌───────────────────────┐                    ┌──────────────────────────┐  │
│  │   Service A (Billing) │                    │   Service B (Inference)  │  │
│  │ ┌───────────────────┐ │                    │ ┌──────────────────────┐ │  │
│  │ │ Capability Vault  │ │                    │ │ Capability Vault     │ │  │
│  │ │ (Excess API Qs)   │ │                    │ │ (Excess GPU VRAM)    │ │  │
│  │ └─────────┬─────────┘ │                    │ └──────────┬───────────┘ │  │
│  │           │           │                    │            │             │  │
│  │ ┌─────────▼─────────┐ │                    │ ┌──────────▼───────────┐ │  │
│  │ │  Utility Profile  │ │                    │ │  Utility Profile     │ │  │
│  │ │ (Urgency Curve)   │ │                    │ │ (Urgency Curve)      │ │  │
│  │ └─────────┬─────────┘ │                    │ └──────────┬───────────┘ │  │
│  └───────────┼───────────┘                    └────────────┼─────────────┘  │
│              │                                             │                │
│              ▼                                             ▼                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │               CLOSED-FORM NASH BARGAINING SOLVER (NBS)                │  │
│  │       Max (U_A(q_B) - c_A - d_A) * (U_B(q_A) - c_B - d_B) in <500μs   │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      │                                      │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │             ATOMIC CAPABILITY HANDOVER ESCROW (ACHE)                  │  │
│  │    Two-Phase Lock -> HMAC-SHA256 Signed Leases -> Quota Commitment    │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      │                                      │
│              ┌───────────────────────┴───────────────────────┐              │
│              ▼                                               ▼              │
│  ┌───────────────────────┐                    ┌──────────────────────────┐  │
│  │ Leased GPU Capability │                    │ Leased API Rate Limit    │  │
│  │ Active on Service A   │                    │ Active on Service B      │  │
│  └───────────────────────┘                    └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1 Capability Vault
- Stores local capability assets (`API_RATE_LIMIT`, `QUEUE_PRIORITY_SLOT`, `GPU_VRAM_MB_SEC`, `CACHE_RESIDENCY_SLOT`, `BURST_CPU_CREDIT`).
- Generates HMAC-SHA256 signatures over canonical descriptors.
- Provides atomic reservation locks and allocation commits.

### 2.2 Nash Bargaining Solver (NBS)
- Computes Pareto-optimal barter quantities $(q_{A \to B}^*, q_{B \to A}^*)$ by maximizing the Nash Product.
- Two-phase coarse grid scan + coordinate descent bisection optimizer converges in **$<500\mu\text{s}$**.

### 2.3 Atomic Capability Handover Escrow (ACHE)
- Two-phase capability swap protocol: reserves quantities in both vaults before minting bilateral signed leases.
- Guaranteed zero-risk atomicity: either both services receive signed leases or all reservations roll back immediately.

### 2.4 Capability Proxy & Quota Tracker
- Intercepts outbound calls and meters request volume against active leased capabilities.
- Enforces TTL expiration and automatic quota restitution.

### 2.5 Autonomous Clearing House & Equilibrium Tracker
- Discovers complementary peer offers across the network and executes automated clearing matches.
- Tracks real-time empirical shadow exchange rates ($\lambda$) and aggregate social welfare gains.
