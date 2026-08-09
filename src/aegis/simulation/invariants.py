"""
State Invariant Definitions for Shadow State Simulation in AegisKernel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from aegis.core.types import InvariantViolation, Severity


@dataclass
class StateInvariant:
    """
    Defines a formal state invariant that must hold across all state mutations.
    """
    invariant_id: str
    name: str
    description: str
    check_fn: Callable[[Dict[str, Any], Dict[str, Any]], bool]  # (pre_state, post_state) -> is_valid
    severity: Severity = Severity.CRITICAL
    remediation_suggestion: Optional[str] = None

    def verify(self, pre_state: Dict[str, Any], post_state: Dict[str, Any]) -> Optional[InvariantViolation]:
        """Runs the invariant check and returns InvariantViolation if it fails."""
        try:
            passed = self.check_fn(pre_state, post_state)
            if not passed:
                return InvariantViolation(
                    rule_id=self.invariant_id,
                    rule_name=self.name,
                    severity=self.severity,
                    message=f"State Invariant Breach: {self.description}",
                    expected_condition="Invariant predicate evaluates to True",
                    actual_value="Invariant predicate failed on post-mutation state",
                    remediation_suggestion=self.remediation_suggestion,
                )
            return None
        except Exception as e:
            return InvariantViolation(
                rule_id=self.invariant_id,
                rule_name=self.name,
                severity=Severity.CRITICAL,
                message=f"State Invariant evaluation error: {str(e)}",
                remediation_suggestion="Inspect state structure and invariant check function.",
            )


# Built-in standard enterprise financial and data safety invariants
def check_non_negative_balances(pre_state: Dict[str, Any], post_state: Dict[str, Any]) -> bool:
    """Ensures no account balance drops below 0."""
    accounts = post_state.get("accounts", {})
    if isinstance(accounts, dict):
        for acc_id, data in accounts.items():
            if isinstance(data, dict) and "balance" in data:
                if data["balance"] < 0:
                    return False
    return True


def check_max_row_deletion_limit(pre_state: Dict[str, Any], post_state: Dict[str, Any]) -> bool:
    """Ensures agent cannot delete more than 20% of records in a single step."""
    pre_records = pre_state.get("records", {})
    post_records = post_state.get("records", {})
    if isinstance(pre_records, dict) and isinstance(post_records, dict):
        pre_len = len(pre_records)
        post_len = len(post_records)
        if pre_len > 10 and (pre_len - post_len) > (pre_len * 0.20):
            return False
    return True


DEFAULT_STATE_INVARIANTS: List[StateInvariant] = [
    StateInvariant(
        invariant_id="INV_NON_NEGATIVE_BALANCE",
        name="Account Balance Non-Negativity Invariant",
        description="Account balances must remain non-negative after any mutation.",
        check_fn=check_non_negative_balances,
        severity=Severity.CRITICAL,
        remediation_suggestion="Adjust mutation amount so account balance does not drop below zero.",
    ),
    StateInvariant(
        invariant_id="INV_MAX_ROW_DELETION",
        name="Mass Record Deletion Protection Invariant",
        description="Single agent step cannot delete more than 20% of database records.",
        check_fn=check_max_row_deletion_limit,
        severity=Severity.CRITICAL,
        remediation_suggestion="Perform batch deletions through approved human-verified migration workflows.",
    ),
]
