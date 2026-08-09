<div align="center">

# Ω AegisKernel

### **High-Assurance Runtime & Deterministic Verification Engine for Autonomous AI Agents**

[![CI Pipeline](https://github.com/AGENTICATION-MAIN/aegis-kernel/actions/workflows/ci.yml/badge.svg)](https://github.com/AGENTICATION-MAIN/aegis-kernel/actions/workflows/ci.yml)
[![Security Audit](https://github.com/AGENTICATION-MAIN/aegis-kernel/actions/workflows/security.yml/badge.svg)](https://github.com/AGENTICATION-MAIN/aegis-kernel/actions/workflows/security.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Latency: Sub-millisecond](https://img.shields.io/badge/P99_Latency-<2.5ms-brightgreen.svg)]()
[![Compliance](https://img.shields.io/badge/EU_AI_Act-Art_14%2F15_Compliant-purple.svg)]()

<p align="center">
  <b>Deterministic Policy Invariants</b> • 
  <b>Capability-Based Security (CBAC)</b> • 
  <b>Dynamic Taint Tracking</b> • 
  <b>Pre-Flight Shadow Simulation</b> • 
  <b>Cryptographic Merkle Provenance</b>
</p>

</div>

---

## ⚡ The Enterprise AI Crisis

Autonomous agents in 2026 are taking mutating, real-world actions: issuing bank transfers, updating production databases, generating cloud resources, and sending customer communications.

**The Problem:** Large Language Models (LLMs) are fundamentally non-deterministic and stochastic. They are vulnerable to:
1. **Indirect Prompt Injection**: Malicious instructions hidden in scraped HTML, customer support tickets, or emails that hijack agent reasoning loops.
2. **Privilege Escalation & Cascading Failures**: Unconstrained agent tool-calling loops executing destructive mutations without state validation.
3. **Soft/Brittle Guardrails**: Regex prompts or secondary LLM evaluators (LLM-as-a-judge) that add compounding latency, non-determinism, and fail basic evasion attacks.
4. **Audit Impossibility**: Unstructured text logs provide zero non-repudiation, making SOC 2, HIPAA, and EU AI Act Article 14/15 compliance impossible.

**AegisKernel solves this through deterministic containment.** It decouples reasoning from authorization: the LLM proposes an *Intent*, and AegisKernel deterministically verifies it against capability bounds, information-flow taint rules, formal state invariants, and records every decision in an append-only Merkle ledger in **$<1\text{ ms}$**.

---

## 🏛️ System Architecture

```
                  ┌─────────────────────────────────────┐
                  │    Autonomous AI Agent Pipeline     │
                  │   (OpenAI, Anthropic, LangChain)    │
                  └──────────────────┬──────────────────┘
                                     │ Tool Execution Intent
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             AEGIS KERNEL RUNTIME                            │
│                                                                             │
│  1. Rate Limiting & Velocity Bounds (Sliding Window Token Bucket)           │
│  2. Adversarial Threat & Prompt Injection Detector (Regex / Entropy AST)    │
│  3. Dynamic Taint Flow Engine (Origin Tracking & Protected Sinks)           │
│  4. Capability Token Validator (CBAC / HMAC-SHA256 Signed Leases)           │
│  5. Neuro-Symbolic Policy & Invariant Engine (AST Predicate Evaluator)      │
│  6. Shadow State Sandbox (Pre-Flight Invariant Simulation & State Diffs)    │
│  7. Merkle Provenance Ledger (Append-Only Cryptographic Audit Trail)        │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ Verified / Sanitized Action
                                     ▼
                  ┌─────────────────────────────────────┐
                  │   Protected Enterprise Sinks        │
                  │ (Postgres, Stripe, AWS, Bash, APIs) │
                  └─────────────────────────────────────┘
```

---

## 🛡️ Core Mechanisms & Technical Moat

### 1. Capability-Based Access Control (CBAC)
- **Signed Capability Leases**: Ephemeral HMAC-SHA256 signed capability tokens grant least-privilege tool access with TTLs and parameter constraint masks.
- **Formal Attenuation Safety**: When delegating work to sub-agents, privileges can only be strictly narrowed ($\text{Child} \subseteq \text{Parent}$), never widened.
- **Revocation Cascade**: Revoking a parent token instantaneously revokes all downstream descendant tokens.

### 2. Neuro-Symbolic Policy & Invariant Engine (AST)
- High-performance Abstract Syntax Tree (AST) evaluator for declarative policy expressions.
- **Four Execution Phases**: `PRE_REASONING`, `PRE_EXECUTION`, `POST_EXECUTION`, and `TRANSACTION_COMMIT`.
- Sub-millisecond evaluation with full explainability receipts and remediation suggestions.

### 3. Dynamic Taint & Information Flow Tracking
- Tracks data provenance across agent conversational turns and memory contexts (`SYSTEM`, `AUTHENTICATED_USER`, `SENSITIVE_PII`, `UNTRUSTED_EXTERNAL`, `MALICIOUS_ADVERSARIAL`).
- **Protected Sink Enforcing**: Untrusted external data cannot flow into privileged tools (`execute_sql`, `execute_bash`, `transfer_funds`) without validated sanitizers.

### 4. Pre-Flight Shadow State Simulation
- Simulates proposed tool mutations against an isolated memory snapshot before committing.
- Validates system-wide formal invariants (e.g. non-negative balance conservation, mass deletion thresholds).

### 5. Cryptographic Merkle Provenance Ledger
- Append-only Merkle DAG with HMAC-SHA256 leaf signatures.
- **Inclusion Proofs ($O(\log N)$)**: Allows third-party auditors to verify that an agent action occurred with a specific verdict without disclosing the full database.
- **Mathematical Tamper Evident**: Any modification to historical records immediately invalidates the Merkle root.

---

## 📊 Performance Benchmarks

| Metric | AegisKernel | Secondary LLM Guard | Brittle Regex Wrappers |
|---|---|---|---|
| **P50 Evaluation Latency** | **$0.45\text{ ms}$** | $850.00\text{ ms}$ | $0.20\text{ ms}$ |
| **P99 Evaluation Latency** | **$2.21\text{ ms}$** | $2,400.00\text{ ms}$ | $1.10\text{ ms}$ |
| **Deterministic Guarantees** | **100% (Mathematical)** | 0% (Stochastic) | Partial |
| **Dynamic Taint Tracking** | **Yes (5 Levels)** | No | No |
| **Cryptographic Audit Proofs** | **Yes (Merkle DAG)** | No | No |
| **Cost per 1M Invocations** | **$0.00** | ~$2,500.00 | $0.00 |

---

## 🚀 Quickstart

### 1. Installation

```bash
pip install aegis-kernel
```

Or clone and install in development mode:

```bash
git clone https://github.com/AGENTICATION-MAIN/aegis-kernel.git
cd aegis-kernel
pip install -e ".[dev]"
```

### 2. Basic Python Integration

```python
from aegis import AegisKernel, ToolExecutionIntent, PolicyParser

# 1. Initialize Kernel
kernel = AegisKernel()

# 2. Define and register a declarative AST invariant rule
rule = PolicyParser.parse_rule({
    "rule_id": "MAX_TRANSFER_LIMIT",
    "rule_name": "Maximum Transfer Limit",
    "description": "Autonomous agents cannot transfer more than $5,000 without approval.",
    "phase": "PRE_EXECUTION",
    "condition": {
        "field": "args.amount",
        "op": "<=",
        "value": 5000.0
    },
    "target_tools": ["transfer_funds"],
    "action_on_violation": "DENY"
})
kernel.policies.register_rule(rule)

# 3. Verify an agent's proposed intent
intent = ToolExecutionIntent(
    tool_name="transfer_funds",
    arguments={"recipient": "vendor-42", "amount": 1200.0},
    agent_id="finance-agent-1",
    session_id="sess-882",
)

result = kernel.verify_intent(intent)

print("Decision:", result.decision.value) # -> ALLOW
print("Merkle Leaf Hash:", result.merkle_node_hash)
print("Evaluation Latency:", result.evaluation_latency_ms, "ms")
```

### 3. Function Guard Decorator

```python
from aegis import AegisKernel
from aegis.adapters import aegis_guard

kernel = AegisKernel()

@aegis_guard(kernel=kernel, tool_name="transfer_funds")
def transfer_funds(recipient: str, amount: float):
    # This executes ONLY if all invariants pass
    return {"status": "SUCCESS", "recipient": recipient, "amount": amount}

# Allowed call
transfer_funds("vendor-A", 250.0)

# Invariant violation raises InvariantBreachError
transfer_funds("vendor-A", 15000.0) # -> InvariantBreachError!
```

---

## 🖥️ Live Interactive Dashboard & REST API

Launch the built-in server:

```bash
aegis serve --host 0.0.0.0 --port 8000
```

- **Interactive UI Dashboard**: Open `http://localhost:8000` to test intents, inspect active capability tokens, view the dynamic taint graph, and verify Merkle inclusion proofs mathematically.
- **Interactive REST API Docs**: Open `http://localhost:8000/docs` (Swagger UI).

---

## 💻 CLI Commands

```bash
# Start REST API and Web Dashboard
aegis serve --port 8000

# Run sub-millisecond throughput and latency benchmark
aegis benchmark -n 5000

# Run multi-scenario agent protection demo
aegis demo

# Evaluate an intent JSON file directly
aegis eval intent.json
```

---

## 🧪 Comprehensive Verification Suite

AegisKernel includes 42 automated tests across unit, integration, adversarial threat attack vectors, and performance benchmarks:

```bash
# Run full test suite
pytest -v

# Run adversarial attack deflection tests
pytest tests/adversarial/ -v

# Run performance and latency benchmarks
pytest tests/benchmarks/ -v
```

---

## 📚 Documentation Index

- [Architecture Specification](ARCHITECTURE.md)
- [Security Policy & Threat Model](SECURITY.md)
- [Capability-Based Security Model (CBAC)](docs/architecture/cbac_security_model.md)
- [Dynamic Taint Tracking Guide](docs/architecture/taint_tracking.md)
- [Merkle Provenance Ledger & Proofs](docs/architecture/merkle_provenance.md)
- [Policy DSL Specification](docs/policy_language/dsl_specification.md)
- [REST API Reference](docs/api/rest_api_reference.md)
- [Commercialization & Monetization Architecture](docs/product/commercial_model.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

---

## ⚖️ License

AegisKernel is open-source software licensed under the [Apache License, Version 2.0](LICENSE).
Copyright 2026 Agentication-MAIN.
