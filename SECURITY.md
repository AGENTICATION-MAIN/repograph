# AegisKernel Security Policy & Threat Model

## 1. Security Architecture & Threat Model

AegisKernel is designed to operate in hostile, untrusted, and multi-tenant AI environments where agents interact with external untrusted inputs (web pages, customer emails, third-party APIs).

### Primary Threat Vectors Addressed:
1. **Direct & Indirect Prompt Injection**: Malicious instructions embedded in scraped HTML, email bodies, or API outputs attempting to override agent instructions.
2. **Capability & Token Forgery**: Unauthorized actors attempting to forge capability tokens or escalate permissions.
3. **Privilege Escalation via Delegation**: Sub-agents attempting to gain privileges not held by their parent.
4. **Data Exfiltration & Taint Breach**: Untrusted data flowing directly into high-privilege execution sinks (SQL, Shell, Payment APIs).
5. **State Invariant Breaches**: Agents proposing out-of-order or corrupting mutations (e.g. overdrafting accounts, dropping database tables).
6. **Audit Trail Tampering & Non-Repudiation Failures**: Modification of historical execution logs by rogue agents or compromised operators.

---

## 2. Cryptographic Security Standards

- **HMAC-SHA256**: Used for capability token signing, leaf record signing, and audit proof validation.
- **SHA-256 Merkle DAG**: Used for cryptographic ledger root calculation and inclusion proofs.
- **Timing Attack Mitigation**: Uses `hmac.compare_digest` for all cryptographic signature comparisons to prevent timing side-channel attacks.
- **Secret Zeroization**: Configuration representations scrub secret keys before serialization or API output.

---

## 3. Reporting a Vulnerability

If you discover a security vulnerability in AegisKernel, please report it responsibly:

1. **Email**: `security@agentication.com` (or create a private GitHub Security Advisory).
2. **Details**: Include proof-of-concept intent payloads, policy AST rules, and reproduction steps.
3. **Disclosure Policy**: We follow coordinated disclosure and aim to acknowledge reports within 24 hours and provide remediations within 7 days.
