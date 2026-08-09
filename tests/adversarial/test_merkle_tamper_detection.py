"""
Adversarial Tests: Merkle Tree Cryptographic Tampering and Bit-Flip Attacks.
"""

import pytest
from aegis.core.types import Decision, ToolExecutionIntent, VerificationResult
from aegis.ledger.merkle import MerkleLedger
from aegis.ledger.verifier import AuditVerifier


def test_merkle_proof_tampering_detection(secret_key):
    ledger = MerkleLedger(secret_key=secret_key)

    for i in range(8):
        intent = ToolExecutionIntent(
            tool_name="transfer",
            arguments={"amount": i * 100},
            agent_id="agent-0",
            session_id="sess-0",
        )
        res = VerificationResult(
            decision=Decision.ALLOW,
            intent_id=intent.intent_id,
            agent_id=intent.agent_id,
            session_id=intent.session_id,
            reason="Verified",
        )
        ledger.record_decision(intent, res)

    proof = ledger.generate_proof(4)
    assert AuditVerifier.verify_proof(proof.to_dict()) is True

    # 1. Attacker tampers with the sibling hash in the audit path
    tampered_dict1 = proof.to_dict()
    tampered_dict1["audit_path"][0]["hash"] = "a" * 64
    assert AuditVerifier.verify_proof(tampered_dict1) is False

    # 2. Attacker tampers with root hash
    tampered_dict2 = proof.to_dict()
    tampered_dict2["root_hash"] = "f" * 64
    assert AuditVerifier.verify_proof(tampered_dict2) is False

    # 3. Attacker alters leaf index / path direction
    tampered_dict3 = proof.to_dict()
    tampered_dict3["audit_path"][0]["direction"] = "L" if tampered_dict3["audit_path"][0]["direction"] == "R" else "R"
    assert AuditVerifier.verify_proof(tampered_dict3) is False
