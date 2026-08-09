"""
Standalone Cryptographic Audit Verifier for Third-Party Auditors.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional

from aegis.core.types import MerkleAuditProof
from aegis.ledger.merkle import MerkleLedger, hash_pair


class AuditVerifier:
    """
    Lightweight zero-dependency cryptographic audit verifier.
    Can be used by client applications and regulatory compliance inspectors.
    """

    @staticmethod
    def verify_proof(proof_data: Dict[str, Any]) -> bool:
        """Verifies a Merkle inclusion proof dictionary."""
        try:
            leaf_hash = proof_data["leaf_hash"]
            root_hash = proof_data["root_hash"]
            audit_path = proof_data["audit_path"]

            curr = leaf_hash
            for step in audit_path:
                direction = step["direction"]
                sibling = step["hash"]
                if direction == "R":
                    curr = hash_pair(curr, sibling)
                elif direction == "L":
                    curr = hash_pair(sibling, curr)
                else:
                    return False

            return curr == root_hash
        except Exception:
            return False
