# AegisKernel: System Architecture Specification

## 1. System Overview & Philosophy

**AegisKernel** is a high-assurance, neuro-symbolic agent execution runtime designed to sit between stochastic Large Language Models (LLMs) and mutating enterprise environments (databases, payment APIs, cloud infrastructure, file systems).

Modern AI agents suffer from fundamental safety limitations:
- **Non-deterministic reasoning**: Prompts can produce invalid, out-of-bounds, or hallucinated arguments.
- **Indirect Prompt Injection**: External web text, emails, or data payloads can hijack agent reasoning loops.
- **Privilege Escalation**: Standard RBAC cannot handle dynamic state conditions or tool delegation trees.
- **Unverifiable Audits**: Plaintext log files provide zero non-repudiation guarantees.

AegisKernel solves these problems through **deterministic containment**: mathematical invariant verification, dynamic information-flow taint tracking, attenuable capability tokens, shadow-state pre-flight simulations, and cryptographic Merkle provenance ledgers.

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

## 2. Core Subsystems

### 2.1 Capability-Based Access Control (CBAC)
- **Capability Tokens**: Cryptographically signed leases granting ephemeral execution rights.
- **Parameter Masks**: Precise range, regex, and allowable set constraints for each tool parameter.
- **Attenuation Invariant**: A token can only be delegated with strictly narrowed (equal or subset) privileges:
  $$\text{Privileges}(\text{Child}) \subseteq \text{Privileges}(\text{Parent})$$
- **Revocation Cascade**: Revoking a parent token automatically and instantaneously revokes all delegated descendant tokens.

### 2.2 Neuro-Symbolic Policy & AST Invariant Engine
- **Abstract Syntax Tree (AST)**: Expressions are compiled into typed nodes (`BinaryOp`, `LogicalOp`, `UnaryOp`, `FieldPath`, `FunctionCall`).
- **Four Execution Phases**:
  1. `PRE_REASONING`: Inbound prompt and user intent gating.
  2. `PRE_EXECUTION`: Tool name, arguments, and session invariant checks.
  3. `POST_EXECUTION`: Tool output inspection and data exfiltration / PII scrubbing.
  4. `TRANSACTION_COMMIT`: Cross-step aggregate velocity checks.
- **Evaluation Performance**: Pre-indexed rule evaluations achieve P99 latency $<2.5\text{ ms}$.

### 2.3 Dynamic Taint & Information Flow Tracker
- **Taint Hierarchy**:
  $$\text{SYSTEM (0)} \prec \text{AUTHENTICATED\_USER (1)} \prec \text{SENSITIVE\_PII (2)} \prec \text{UNTRUSTED\_EXTERNAL (3)} \prec \text{MALICIOUS\_ADVERSARIAL (4)}$$
- **Propagation Rules**: Tool arguments inherit the maximum taint of their contributing context:
  $$\tau(\text{arg}) = \max_{s \in \text{Sources}} \tau(s)$$
- **Protected Sinks**: Critical tools (`execute_sql`, `execute_bash`, `transfer_funds`) enforce strict taint ceilings that reject untrusted data unless processed by an approved sanitizer.

### 2.4 Shadow State Sandbox & Pre-Flight Invariants
- Mutating tools are simulated against an in-memory copy of state before committing.
- Formal invariants (e.g. non-negative account balances, batch deletion ceilings) are verified on simulated state.
- If invariants pass, the computed `StateDiff` is committed to live state; otherwise, the transaction is rejected without side-effects.

### 2.5 Cryptographic Merkle Provenance Ledger
- Append-only cryptographic log using SHA-256 and HMAC-SHA256 signatures.
- Computes dynamic Merkle Tree root $R$:
  $$H_{\text{parent}} = \text{SHA-256}(H_{\text{left}} \parallel H_{\text{right}})$$
- **Inclusion Proofs**: Produces $O(\log N)$ logarithmic cryptographic inclusion proofs verifiable by third-party auditors without sharing the full database.
- **Tamper Evident**: Any modification to historical records alters the Merkle root and invalidates HMAC signatures.

---

## 3. Data Flow & Execution Sequence

1. **Agent Intent Generation**: Agent emits a tool call intent $I = (\text{tool}, \text{args}, \text{agent\_id}, \text{session\_id})$.
2. **Kernel Interception**: Intercepted by `OpenAIToolAdapter`, `AnthropicToolAdapter`, or `@aegis_guard`.
3. **Pipeline Evaluation**:
   - Rate limiting verified.
   - Adversarial patterns scanned.
   - Dynamic taint verified against sink rules.
   - Capability token verified (signature, expiration, scope).
   - AST invariant predicates evaluated.
   - Shadow state simulated.
4. **Receipt Generation**: Verified decision is appended to Merkle Ledger and signed.
5. **Execution & Post-Verification**: Tool callable is executed; output is checked for PII leaks.
