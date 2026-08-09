# Pactum Security Policy & Threat Model

## 1. Threat Model

Pactum operates in distributed, multi-tenant microservice and autonomous agent environments.

### Primary Threat Vectors Mitigated:
1. **Free-Riding & Over-Promising**: A service attempts to barter capability units it does not actually own. Mitigated via atomic vault balance reservation locks.
2. **Lease Tampering & Forgery**: A rogue process creates fake lease credentials to consume unauthorized resources. Mitigated via HMAC-SHA256 cryptographic signatures.
3. **Counterparty Default**: A service attempts to consume its counterparty's lease while withholding its own promised capacity. Mitigated via Two-Phase Atomic Capability Escrow (ACHE).
4. **Timing Attacks**: All cryptographic signature verifications use timing-safe `hmac.compare_digest`.

---

## 2. Vulnerability Reporting

Please report security issues to `security@agentication.com`. We aim to acknowledge reports within 24 hours and patch vulnerabilities within 7 days.
