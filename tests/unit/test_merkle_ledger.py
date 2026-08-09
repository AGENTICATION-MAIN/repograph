"""
Unit tests for Cryptographic Merkle Ledger and Inclusion Proofs.
"""

import pytest
from aegis.core.types import Decision, ToolExecutionIntent, VerificationResult
from aegis.ledger.merkle import MerkleLedger, hash_pair, sha256_hash
from aegis.ledger.verifier import AuditVerifier


def test_merkle_ledger_recording_and_root(secret_key):
    ledger = MerkleLedger(secret_key=secret_key)
    assert ledger.get_root_hash() == MerkleLedger.GENESIS_HASH

    intents = []
    for i in range(4):
        intent = ToolExecutionIntent(
            tool_name="test_tool",
            arguments={"step": i},
            agent_id="test-agent",
            session_id="test-session",
        )
        res = VerificationResult(
            decision=Decision.ALLOW,
            intent_id=intent.intent_id,
            agent_id=intent.agent_id,
            session_id=intent.session_id,
            reason="Approved",
        )
        rec = ledger.record_decision(intent, res)
        assert rec.verify_leaf_hash() if hasattr(rec, 'verify_leaf_hash') else rec.leaf_hash != ""
        intents.append(intent)

    assert len(ledger) == 4
    root = ledger.get_root_hash()
    assert len(root) == 64
    assert root != MerkleLedger.GENESIS_HASH


def test_merkle_inclusion_proof_and_verification(secret_key):
    ledger = MerkleLedger(secret_key=secret_key)

    intents = []
    for i in range(7):  # Non-power-of-2 test
        intent = ToolExecutionIntent(
            tool_name="tool",
            arguments={"val": i * 10},
            agent_id="agent",
            session_id="sess",
        )
        res = VerificationResult(
            decision=Decision.ALLOW,
            intent_id=intent.intent_id,
            agent_id=intent.agent_id,
            session_id=intent.session_id,
            reason="OK",
        )
        ledger.record_decision(intent, res)
        intents.append(intent)

    # Test inclusion proof for index 3
    proof3 = ledger.generate_proof(3)
    assert proof3.leaf_index == 3
    assert proof3.total_leaves == 7
    assert MerkleLedger.verify_proof_static(proof3) is True
    assert AuditVerifier.verify_proof(proof3.to_dict()) is True

    # Test inclusion proof for last item (index 6)
    proof6 = ledger.generate_proof(6)
    assert proof6.leaf_index == 6
    assert MerkleLedger.verify_proof_static(proof6) is True
    assert AuditVerifier.verify_proof(proof6.to_dict()) is True


def test_chain_integrity_and_tamper_detection(secret_key):
    ledger = MerkleLedger(secret_key=secret_key)

    for i in range(3):
        intent = ToolExecutionIntent(
            tool_name="tool",
            arguments={"val": i},
            agent_id="agent",
            session_id="sess",
        )
        res = VerificationResult(
            decision=Decision.ALLOW,
            intent_id=intent.intent_id,
            agent_id=intent.agent_id,
            session_id=intent.session_id,
            reason="OK",
        )
        ledger.record_decision(intent, res)

    # Verify initial integrity
    ok, err = ledger.verify_ledger_integrity()
    assert ok is True
    assert err is None

    # Tamper with middle record
    ledger._records[1].decision = "DENY"
    ok, err = ledger.verify_ledger_integrity()
    assert ok is False
    assert "Leaf hash altered" in err
