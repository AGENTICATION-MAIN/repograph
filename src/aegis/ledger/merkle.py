"""
Merkle Tree and Cryptographic Provenance Ledger for AegisKernel.

Provides append-only, mathematically verifiable audit trails with inclusion proofs.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aegis.core.exceptions import MerkleIntegrityError
from aegis.core.types import (
    MerkleAuditProof,
    ToolExecutionIntent,
    VerificationResult,
)

logger = logging.getLogger("aegis.ledger")


def sha256_hash(data: bytes) -> str:
    """Computes SHA-256 hex digest."""
    return hashlib.sha256(data).hexdigest()


def hash_pair(left_hex: str, right_hex: str) -> str:
    """Computes parent hash from left and right children."""
    combined = (left_hex + right_hex).encode("utf-8")
    return sha256_hash(combined)


@dataclass
class MerkleRecord:
    """
    Immutable individual record stored in the ledger leaf.
    """
    index: int
    record_id: str
    timestamp: float
    prev_hash: str
    intent_id: str
    agent_id: str
    session_id: str
    tool_name: str
    arguments_hash: str
    decision: str
    reason: str
    violations_count: int
    leaf_hash: str = ""
    signature: str = ""

    def canonical_bytes(self) -> bytes:
        """Returns deterministic serialized byte representation."""
        data = {
            "index": self.index,
            "record_id": self.record_id,
            "timestamp": round(self.timestamp, 4),
            "prev_hash": self.prev_hash,
            "intent_id": self.intent_id,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "tool_name": self.tool_name,
            "arguments_hash": self.arguments_hash,
            "decision": self.decision,
            "reason": self.reason,
            "violations_count": self.violations_count,
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def compute_leaf_hash(self) -> str:
        """Computes SHA-256 leaf hash."""
        h = sha256_hash(self.canonical_bytes())
        self.leaf_hash = h
        return h

    def sign(self, secret_key: str) -> str:
        """Signs the leaf hash using HMAC-SHA256."""
        if not self.leaf_hash:
            self.compute_leaf_hash()
        sig = hmac.new(
            secret_key.encode("utf-8"),
            self.leaf_hash.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        self.signature = sig
        return sig

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "intent_id": self.intent_id,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "tool_name": self.tool_name,
            "arguments_hash": self.arguments_hash,
            "decision": self.decision,
            "reason": self.reason,
            "violations_count": self.violations_count,
            "leaf_hash": self.leaf_hash,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MerkleRecord:
        return cls(
            index=data["index"],
            record_id=data["record_id"],
            timestamp=data["timestamp"],
            prev_hash=data["prev_hash"],
            intent_id=data["intent_id"],
            agent_id=data["agent_id"],
            session_id=data["session_id"],
            tool_name=data["tool_name"],
            arguments_hash=data["arguments_hash"],
            decision=data["decision"],
            reason=data["reason"],
            violations_count=data.get("violations_count", 0),
            leaf_hash=data.get("leaf_hash", ""),
            signature=data.get("signature", ""),
        )


class MerkleLedger:
    """
    Append-Only Cryptographic Merkle Ledger.
    Tracks state transitions and provides inclusion proofs.
    """

    GENESIS_HASH = "0" * 64

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self._records: List[MerkleRecord] = []
        self._records_by_intent: Dict[str, MerkleRecord] = {}
        self._lock = threading.RLock()

    def __len__(self) -> int:
        with self._lock:
            return len(self._records)

    def record_decision(
        self,
        intent: ToolExecutionIntent,
        result: VerificationResult,
    ) -> MerkleRecord:
        """Appends a new verified execution record to the ledger."""
        with self._lock:
            idx = len(self._records)
            prev_hash = self._records[-1].leaf_hash if idx > 0 else self.GENESIS_HASH

            # Hash the arguments deterministically
            args_bytes = json.dumps(intent.arguments, sort_keys=True, separators=(",", ":")).encode("utf-8")
            args_hash = sha256_hash(args_bytes)

            rec = MerkleRecord(
                index=idx,
                record_id=f"rec-{idx:08d}",
                timestamp=time.time(),
                prev_hash=prev_hash,
                intent_id=intent.intent_id,
                agent_id=intent.agent_id,
                session_id=intent.session_id,
                tool_name=intent.tool_name,
                arguments_hash=args_hash,
                decision=result.decision.value,
                reason=result.reason,
                violations_count=len(result.violations),
            )
            rec.compute_leaf_hash()
            rec.sign(self.secret_key)

            self._records.append(rec)
            self._records_by_intent[intent.intent_id] = rec

            result.merkle_node_hash = rec.leaf_hash
            result.merkle_root_hash = self.get_root_hash()

            return rec

    def get_root_hash(self) -> str:
        """Computes the root hash of the Merkle tree over all current leaves."""
        with self._lock:
            if not self._records:
                return self.GENESIS_HASH

            current_level = [r.leaf_hash for r in self._records]

            while len(current_level) > 1:
                next_level: List[str] = []
                for i in range(0, len(current_level), 2):
                    left = current_level[i]
                    if i + 1 < len(current_level):
                        right = current_level[i + 1]
                    else:
                        # Odd element: pair with itself (standard Merkle tree convention)
                        right = left
                    next_level.append(hash_pair(left, right))
                current_level = next_level

            return current_level[0]

    def generate_proof(self, index_or_intent_id: Any) -> MerkleAuditProof:
        """
        Generates a cryptographic Merkle inclusion audit proof for a specific record.
        """
        with self._lock:
            if isinstance(index_or_intent_id, str):
                if index_or_intent_id in self._records_by_intent:
                    target_idx = self._records_by_intent[index_or_intent_id].index
                else:
                    raise KeyError(f"Record for intent '{index_or_intent_id}' not found")
            else:
                target_idx = int(index_or_intent_id)

            if target_idx < 0 or target_idx >= len(self._records):
                raise IndexError(f"Index {target_idx} out of bounds (total records: {len(self._records)})")

            target_rec = self._records[target_idx]
            leaf_hash = target_rec.leaf_hash
            total_leaves = len(self._records)

            # Build level-by-level tree and extract sibling hashes
            audit_path: List[Dict[str, str]] = []
            current_level = [r.leaf_hash for r in self._records]
            idx_in_level = target_idx

            while len(current_level) > 1:
                next_level: List[str] = []
                # Check if current target index is even or odd
                if idx_in_level % 2 == 0:
                    # Target is on left, sibling is on right
                    if idx_in_level + 1 < len(current_level):
                        sibling = current_level[idx_in_level + 1]
                    else:
                        sibling = current_level[idx_in_level]
                    audit_path.append({"direction": "R", "hash": sibling})
                else:
                    # Target is on right, sibling is on left
                    sibling = current_level[idx_in_level - 1]
                    audit_path.append({"direction": "L", "hash": sibling})

                # Compute next level
                for i in range(0, len(current_level), 2):
                    left = current_level[i]
                    right = current_level[i + 1] if i + 1 < len(current_level) else left
                    next_level.append(hash_pair(left, right))

                current_level = next_level
                idx_in_level = idx_in_level // 2

            root_hash = current_level[0]
            now = time.time()

            # Sign proof
            proof_bytes = f"{leaf_hash}:{target_idx}:{root_hash}:{now}".encode("utf-8")
            sig = hmac.new(self.secret_key.encode("utf-8"), proof_bytes, hashlib.sha256).hexdigest()

            return MerkleAuditProof(
                leaf_hash=leaf_hash,
                leaf_index=target_idx,
                total_leaves=total_leaves,
                audit_path=audit_path,
                root_hash=root_hash,
                timestamp=now,
                signature=sig,
            )

    @classmethod
    def verify_proof_static(cls, proof: MerkleAuditProof) -> bool:
        """
        Pure static mathematical verification of a Merkle inclusion proof.
        Requires NO access to the underlying database!
        """
        curr = proof.leaf_hash
        for step in proof.audit_path:
            direction = step["direction"]
            sibling = step["hash"]
            if direction == "R":
                curr = hash_pair(curr, sibling)
            elif direction == "L":
                curr = hash_pair(sibling, curr)
            else:
                return False
        return curr == proof.root_hash

    def verify_ledger_integrity(self) -> Tuple[bool, Optional[str]]:
        """
        Verifies full cryptographic chain integrity:
        1. Checks previous hash links
        2. Re-computes leaf hashes
        3. Verifies HMAC signatures
        """
        with self._lock:
            for i, rec in enumerate(self._records):
                # Verify prev_hash link
                expected_prev = self._records[i - 1].leaf_hash if i > 0 else self.GENESIS_HASH
                if rec.prev_hash != expected_prev:
                    return False, f"PrevHash mismatch at index {i}: expected {expected_prev}, got {rec.prev_hash}"

                # Verify leaf hash recalculation
                recomputed = sha256_hash(rec.canonical_bytes())
                if rec.leaf_hash != recomputed:
                    return False, f"Leaf hash altered at index {i}: expected {recomputed}, got {rec.leaf_hash}"

                # Verify HMAC signature
                expected_sig = hmac.new(
                    self.secret_key.encode("utf-8"),
                    rec.leaf_hash.encode("utf-8"),
                    hashlib.sha256
                ).hexdigest()
                if not hmac.compare_digest(rec.signature, expected_sig):
                    return False, f"Signature invalid at index {i}"

            return True, None

    def get_records(self, limit: int = 100, offset: int = 0) -> List[MerkleRecord]:
        """Retrieves paginated ledger records."""
        with self._lock:
            return list(self._records[offset : offset + limit])
