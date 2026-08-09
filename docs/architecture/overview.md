# AegisKernel Architecture Overview

AegisKernel delivers deterministic containment for autonomous AI agents.

## Core Pillars

1. **Deterministic Guarantees**: While LLM reasoning is probabilistic, tool authorization and state transitions are deterministic and provable.
2. **Zero-Trust Least Privilege**: Agents operate with ephemeral, cryptographically bounded capability tokens rather than static long-lived credentials.
3. **Information-Flow Safety**: Untrusted inputs (web scraping, third-party data) cannot cross into privileged execution sinks without formal sanitization.
4. **Non-Repudiation**: Every decision is anchored in a Merkle DAG with cryptographic inclusion proofs for regulatory compliance (EU AI Act, SOC 2, HIPAA, ISO 42001).
