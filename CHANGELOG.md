# Changelog

All notable changes to AegisKernel will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-09

### Added
- **Core Verification Runtime**: High-performance neuro-symbolic agent execution guard.
- **Capability-Based Access Control (CBAC)**: HMAC-SHA256 signed capability tokens with attenuation safety invariants and cascade revocation.
- **Neuro-Symbolic Policy & Invariant Engine**: AST-based declarative predicate evaluator supporting multi-phase evaluation (`PRE_REASONING`, `PRE_EXECUTION`, `POST_EXECUTION`, `TRANSACTION_COMMIT`).
- **Dynamic Taint & Information Flow Tracker**: Multi-level taint tracking (`SYSTEM` to `MALICIOUS_ADVERSARIAL`) with protected sink enforcement and data sanitizers.
- **Shadow State Sandbox**: In-memory pre-flight simulation for mutating tools with state diff computation and formal invariant checking.
- **Cryptographic Merkle Provenance Ledger**: Append-only tamper-evident Merkle ledger with HMAC-SHA256 leaf signing, Merkle root calculation, and $O(\log N)$ inclusion proof generation.
- **Adversarial Threat Deflector**: Pattern and entropy scanners for indirect prompt injection, DAN jailbreaks, delimiter hijacking, and shell injection.
- **Agent Framework Adapters**: Built-in adapters for OpenAI tool calling format, Anthropic Claude tool use format, and `@aegis_guard` Python decorator.
- **FastAPI REST API & Interactive UI Dashboard**: Endpoints for verification, capability minting, policy management, ledger inspection, and cryptographic proof verification.
- **CLI & Benchmark Suite**: `aegis serve`, `aegis eval`, `aegis benchmark`, `aegis demo`.
- **Complete Test Suite**: 42 automated tests covering unit, integration, adversarial attack vectors, and performance benchmarks.
