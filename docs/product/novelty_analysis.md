# Pactum: Novelty & Prior-Art Analysis

## 1. The Fundamental Problem Framing

Modern distributed software systems suffer from severe **allocative inefficiency** due to rigid, siloed capability boundaries:
- Service A (e.g. `billing-worker`) is allocated 1,000 req/min Stripe API quota, but is using only 50 req/min (950 idle tokens/min).
- Service B (e.g. `checkout-service`) experiences a burst and hits HTTP 429 rate limits, dropping transactions.
- Service C has idle GPU VRAM on an expensive cloud instance ($2.40/hr), but is blocked waiting for queue priority slots owned by Service D.

Currently, **no computational runtime exists** that allows software components to dynamically, autonomously, and atomically barter computing capabilities, rate limits, and memory slices without human intervention, static re-provisioning, or central monetary payment systems.

---

## 2. The Missing Primitive

Pactum introduces a new computational primitive:
**The Coasian Micro-Resource Bartering Runtime.**

Applying Ronald Coase's foundational *Theory of the Firm* and *The Problem of Social Cost* to distributed software:
> *If transaction costs are zero and property rights are well-defined, autonomous economic agents will negotiate Pareto-optimal resource allocations regardless of initial distribution.*

Pactum reduces the transaction cost of cross-service resource reallocation to **$<500\mu\text{s}$** by combining:
1. **Fractional Capability Units (FCUs)**: Cryptographically metered, consumable, time-decaying capability tokens.
2. **Sub-Millisecond Closed-Form Nash Bargaining Solver**: Evaluates marginal utility curves $U_A(x), U_B(x)$ and computes the exact joint-surplus-maximizing trade.
3. **Atomic Capability Handover Escrow (ACHE)**: Two-phase capability swap with cryptographically signed leases and automatic quota revocation.

---

## 3. Prior-Art Collision Matrix

| Existing Category | Exemplars | Why It Fails the Problem | How Pactum is Fundamentally Different |
|---|---|---|---|
| **Service Meshes / Gateways** | Envoy, Istio, Kong | Static routing and uniform rate-limiting policies. No cross-service negotiation. | Pactum dynamically transfers capability quotas across services based on marginal urgency. |
| **Cluster Schedulers** | Kubernetes, Nomad, Mesos | Centralized scheduling of physical pods/VMs at minute-scale intervals. | Pactum operates at sub-millisecond micro-capability granularity (API quotas, priority leases) without restarting pods. |
| **Cloud Auction Systems** | Spot Instances, CloudSim | Centralized monetary bidding for physical VM hardware. | Pactum is decentralized peer-to-peer bartering with zero currency exchange using pure game-theoretic Nash bargaining. |
| **Workflow / Saga Engines** | Temporal, Cadence | Linear forward orchestration with error retry loops. | Pactum is an economic resource exchange runtime, not a task pipeline. |

---

## 4. The "Subtract the AI" Test

If AI is completely removed, does a software invention remain?
**YES.**
Pactum is 100% pure distributed systems engineering, microeconomic theory (Edgeworth box equilibria, Nash cooperative bargaining), and cryptographic capability escrows. It solves an acute problem for both traditional microservices and autonomous AI agents.
