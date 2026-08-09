# AegisKernel Threat Model & Formal Security Analysis

## Threat Class Matrix

| Threat Category | Attack Vector | AegisKernel Defense Mechanism | Outcome |
|---|---|---|---|
| **Indirect Prompt Injection** | Web/Email text instructs agent to exfiltrate passwords | Dynamic Taint Tracker & Adversarial Pattern Scanner | Intent Quarantined / Blocked before reaching Sink |
| **Capability Forgery** | Attacker mints custom capability tokens | HMAC-SHA256 Secret Signing & Verification | Token rejected as unauthenticated signature |
| **Privilege Escalation** | Child agent attempts to broaden tool permissions | Attenuation Invariant ($\text{Child} \subseteq \text{Parent}$) | Delegation rejected with ScopeViolation |
| **Corrupting State Mutation** | Hallucinated negative balance update | Pre-Flight Shadow State Simulation & Invariant Checker | Shadow invariant fails, mutation aborted |
| **Audit Log Tampering** | Malicious insider alters log records | Append-Only Merkle DAG with Cryptographic Hashes | Chain integrity fails, root hash mismatch detected |
