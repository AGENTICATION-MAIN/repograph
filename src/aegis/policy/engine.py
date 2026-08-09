"""
Policy Execution Engine for AegisKernel.

Evaluates symbolic AST invariant rules across execution phases and determines
deterministic authorization outcomes.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from aegis.core.exceptions import InvariantBreachError, PolicyEvaluationError
from aegis.core.types import (
    Decision,
    InvariantViolation,
    PolicyPhase,
    Severity,
    ToolExecutionIntent,
    VerificationResult,
)
from aegis.policy.parser import PolicyParser, PolicyRule

logger = logging.getLogger("aegis.policy")

# Severity order for choosing decisive action
DECISION_PRECEDENCE = {
    Decision.QUARANTINE: 5,
    Decision.DENY: 4,
    Decision.ESCALATE: 3,
    Decision.DEGRADE: 2,
    Decision.ALLOW: 1,
}


class PolicyEngine:
    """
    High-Performance Deterministic Policy Engine.
    Executes compiled AST invariant checks against runtime agent state.
    """

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self._rules: Dict[str, PolicyRule] = {}
        self._rules_by_phase: Dict[PolicyPhase, List[PolicyRule]] = {
            phase: [] for phase in PolicyPhase
        }
        self._lock = threading.RLock()

    def register_rule(self, rule: PolicyRule) -> None:
        """Registers a compiled policy rule."""
        with self._lock:
            self._rules[rule.rule_id] = rule
            self._rebuild_phase_index()

    def register_rules(self, rules: List[PolicyRule]) -> None:
        """Registers multiple rules in batch."""
        with self._lock:
            for rule in rules:
                self._rules[rule.rule_id] = rule
            self._rebuild_phase_index()

    def unregister_rule(self, rule_id: str) -> bool:
        """Removes a rule by ID."""
        with self._lock:
            if rule_id in self._rules:
                del self._rules[rule_id]
                self._rebuild_phase_index()
                return True
            return False

    def get_rule(self, rule_id: str) -> Optional[PolicyRule]:
        with self._lock:
            return self._rules.get(rule_id)

    def list_rules(self, phase: Optional[PolicyPhase] = None) -> List[PolicyRule]:
        with self._lock:
            if phase:
                return list(self._rules_by_phase.get(phase, []))
            return list(self._rules.values())

    def _rebuild_phase_index(self) -> None:
        for phase in PolicyPhase:
            self._rules_by_phase[phase] = [
                r for r in self._rules.values() if r.phase == phase and r.enabled
            ]

    def build_context(
        self,
        intent: ToolExecutionIntent,
        session_context: Optional[Dict[str, Any]] = None,
        result_payload: Optional[Any] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Builds standardized evaluation context dictionary for AST nodes."""
        ctx = {
            "args": intent.arguments,
            "tool_name": intent.tool_name,
            "agent": {
                "id": intent.agent_id,
            },
            "session": {
                "id": intent.session_id,
                **(session_context or {}),
            },
            "metadata": intent.metadata,
            "taint": {
                k: v.to_dict() for k, v in intent.taint_map.items()
            },
            "result": result_payload,
            "timestamp": intent.timestamp,
        }
        if extra:
            ctx.update(extra)
        return ctx

    def evaluate_intent(
        self,
        intent: ToolExecutionIntent,
        phase: PolicyPhase = PolicyPhase.PRE_EXECUTION,
        session_context: Optional[Dict[str, Any]] = None,
        result_payload: Optional[Any] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Decision, List[InvariantViolation], float, int]:
        """
        Evaluates all applicable rules for the specified phase against the intent.
        Returns (Decision, List of InvariantViolations, Latency in ms, Evaluated Rules Count).
        """
        start_time = time.perf_counter()
        violations: List[InvariantViolation] = []
        highest_decision = Decision.ALLOW

        context = self.build_context(intent, session_context, result_payload, extra)

        with self._lock:
            applicable_rules = [
                r for r in self._rules_by_phase.get(phase, [])
                if r.applies_to_tool(intent.tool_name)
            ]

        rules_count = len(applicable_rules)

        for rule in applicable_rules:
            try:
                # The condition represents the REQUIRED INVARIANT.
                # If condition evaluates to False / None, the invariant is VIOLATED.
                is_valid = rule.condition.evaluate(context)
                if not is_valid:
                    violation = InvariantViolation(
                        rule_id=rule.rule_id,
                        rule_name=rule.rule_name,
                        severity=rule.severity,
                        message=rule.description or f"Invariant rule '{rule.rule_name}' failed.",
                        remediation_suggestion=rule.remediation_suggestion,
                    )
                    violations.append(violation)

                    # Update decision if this violation requires stricter action
                    if DECISION_PRECEDENCE[rule.action_on_violation] > DECISION_PRECEDENCE[highest_decision]:
                        highest_decision = rule.action_on_violation

            except Exception as e:
                logger.error(f"Error evaluating rule {rule.rule_id}: {str(e)}")
                # In strict mode, an error in rule evaluation is considered a failure
                if self.strict_mode:
                    violation = InvariantViolation(
                        rule_id=rule.rule_id,
                        rule_name=rule.rule_name,
                        severity=Severity.CRITICAL,
                        message=f"Evaluation error: {str(e)}",
                        remediation_suggestion="Inspect rule expression structure and argument types.",
                    )
                    violations.append(violation)
                    highest_decision = Decision.DENY

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return highest_decision, violations, elapsed_ms, rules_count
