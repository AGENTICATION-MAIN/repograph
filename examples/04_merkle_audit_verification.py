#!/usr/bin/env python3
"""
04_merkle_audit_verification.py — Merkle Provenance Ledger and Tamper Detection Demo.
"""

from aegis import AegisKernel, ToolExecutionIntent
from aegis.ledger import AuditVerifier

def main():
    print("=== AegisKernel Merkle Provenance & Tamper Detection ===")

    kernel = AegisKernel()

    # Record 5 transactions in the Merkle ledger
    intents = []
    for i in range(5):
        intent = ToolExecutionIntent(
            tool_name="process_order",
            arguments={"order_id": f"ORD-{100+i}", "amount": float(50 * (i+1))},
            agent_id="ecom-agent",
            session_id="session-ecom-1",
        )
        kernel.verify_intent(intent)
        intents.append(intent)

    print(f"✓ Recorded {len(kernel.ledger)} transactions into append-only Merkle ledger.")
    print(f"  Current Merkle Root: {kernel.ledger.get_root_hash()}")

    # 1. Generate inclusion proof for transaction #2
    target_intent = intents[2]
    proof = kernel.generate_proof(target_intent.intent_id)
    print(f"\nGenerated Cryptographic Inclusion Proof for Intent: {target_intent.intent_id}")
    print(f"  Leaf Hash:   {proof.leaf_hash}")
    print(f"  Root Hash:   {proof.root_hash}")
    print(f"  Tree Leaves: {proof.total_leaves}")
    print(f"  Proof Path:  {proof.audit_path}")

    # 2. Standalone Verification (Auditor side)
    verified = AuditVerifier.verify_proof(proof.to_dict())
    print(f"\n[Auditor Verification] Proof mathematical validity: {verified}")

    # 3. Simulate Malicious Tampering Attempt
    print("\n--- Simulating Adversarial Tampering Attempt ---")
    corrupted_proof = proof.to_dict()
    # Attacker tries to forge the root or leaf hash
    corrupted_proof["leaf_hash"] = "0" * 64
    tamper_result = AuditVerifier.verify_proof(corrupted_proof)
    print(f"[Auditor Verification] Tampered proof mathematical validity: {tamper_result}")
    assert not tamper_result, "Security check: Tampered proof must fail verification!"
    print("✓ Cryptographic tamper detection successfully prevented fraudulent receipt verification.")

if __name__ == "__main__":
    main()
