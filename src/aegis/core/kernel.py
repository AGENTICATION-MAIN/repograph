"""
Unified AegisKernel Orchestration Engine.

Coordinates capability management, symbolic policy evaluation, dynamic taint tracking,
pre-flight shadow simulation, adversarial threat detection, and cryptographic Merkle provenance.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from aegis.capabilities.manager import CapabilityManager
from aegis.capabilities.token import CapabilityToken
from aegis.core.config import AegisConfig
from aegis.core.exceptions import (
    AegisError,
    CapabilityError,
    InvariantBreachError,
    RateLimitExceededError,
)
from aegis.core.types import (
    Decision,
    InvariantViolation,
    MerkleAuditProof,
    PolicyPhase,
    Severity,
    TaintLevel,
    ToolExecutionIntent,
    VerificationResult,
)
from aegis.ledger.journal import LedgerJournal
from aegis.ledger.merkle import MerkleLedger, MerkleRecord
from aegis.policy.engine import PolicyEngine
from aegis.policy.parser import PolicyParser, PolicyRule
from aegis.security.adversarial import AdversarialDetector
from aegis.security.rate_limiter import SlidingWindowRateLimiter
from aegis.simulation.sandbox import ShadowSandbox
from aegis.taint.tracker import TaintTracker

logger = logging.getLogger("aegis.kernel")


class AegisKernel:
    """
    High-Assurance Agent Execution Kernel and Policy Verification Runtime.
    """

    def __init__(self, config: Optional[AegisConfig] = None):
        self.config = config or AegisConfig()

        # Core Subsystems
        self.capabilities = CapabilityManager(secret_key=self.config.hmac_secret_key)
        self.policies = PolicyEngine(strict_mode=self.config.strict_invariants)
        self.taint_tracker = TaintTracker()
        self.sandbox = ShadowSandbox()
        self.ledger = MerkleLedger(secret_key=self.config.hmac_secret_key)
        self.journal = LedgerJournal(db_path=self.config.db_path)
        self.adversarial_detector = AdversarialDetector()
        self.rate_limiter = SlidingWindowRateLimiter(
            default_limit_per_minute=self.config.default_rate_limit_per_minute
        )

    def verify_intent(
        self,
        intent: ToolExecutionIntent,
        session_context: Optional[Dict[str, Any]] = None,
        phase: PolicyPhase = PolicyPhase.PRE_EXECUTION,
    ) -> VerificationResult:
        """
        Executes full deterministic verification pipeline on a proposed tool intent.
        """
        start_time = time.perf_counter()
        violations: List[InvariantViolation] = []
        highest_decision = Decision.ALLOW
        reason = "All security and policy invariants verified."
        shadow_diff = None
        sanitized_args = None

        # 1. Rate Limiting Check
        rate_key = f"{intent.agent_id}:{intent.tool_name}"
        rate_ok, curr_count, retry_after = self.rate_limiter.check_and_record(rate_key)
        if not rate_ok:
            viol = InvariantViolation(
                rule_id="RATE_LIMIT_EXCEEDED",
                rule_name="Tool Invocation Rate Limit",
                severity=Severity.HIGH,
                message=f"Rate limit exceeded for {rate_key}. Retry after {retry_after}s.",
                expected_condition=f"calls_per_minute <= {self.config.default_rate_limit_per_minute}",
                actual_value=curr_count,
                remediation_suggestion=f"Back off and retry after {retry_after} seconds.",
            )
            violations.append(viol)
            highest_decision = Decision.DENY
            reason = viol.message

        # 2. Adversarial Threat & Prompt Injection Detection (High priority: Quarantines attacks immediately)
        if highest_decision == Decision.ALLOW:
            adv_violations = self.adversarial_detector.scan_intent(intent)
            if adv_violations:
                violations.extend(adv_violations)
                highest_decision = Decision.QUARANTINE
                reason = "Active adversarial payload / prompt injection detected in tool intent."

        # 3. Dynamic Taint Flow Verification
        if highest_decision == Decision.ALLOW and self.config.taint_tracking_enabled:
            taint_violations = self.taint_tracker.verify_intent_taint_safety(intent)
            if taint_violations:
                violations.extend(taint_violations)
                highest_decision = Decision.DENY
                reason = "Tainted untrusted data attempted to reach a protected sink without sanitization."

        # 4. Capability Token Check (if token ID provided)
        if highest_decision == Decision.ALLOW and intent.capability_token_id:
            try:
                taints = self.taint_tracker.compute_intent_taint(intent)
                highest_taint = max([t.level for t in taints.values()], default=TaintLevel.SYSTEM, key=lambda l: l.value)

                self.capabilities.validate_and_consume(
                    token_id=intent.capability_token_id,
                    tool_name=intent.tool_name,
                    arguments=intent.arguments,
                    taint_level=highest_taint,
                )
            except CapabilityError as e:
                viol = InvariantViolation(
                    rule_id="CAPABILITY_VIOLATION",
                    rule_name="Capability Scope Enforcement",
                    severity=Severity.CRITICAL,
                    message=f"Capability violation: {str(e)}",
                    remediation_suggestion="Acquire a valid capability token with appropriate tool scope and arguments.",
                )
                violations.append(viol)
                highest_decision = Decision.DENY
                reason = viol.message

        # 5. Symbolic AST Policy Invariant Evaluation
        if highest_decision == Decision.ALLOW:
            pol_decision, pol_violations, _, rules_evaluated = self.policies.evaluate_intent(
                intent=intent,
                phase=phase,
                session_context=session_context,
            )
            if pol_violations:
                violations.extend(pol_violations)
                highest_decision = pol_decision
                reason = f"Policy invariant violation: {pol_violations[0].message}"
        else:
            rules_evaluated = 0

        # 6. Pre-Flight Shadow State Simulation (if allowed so far and simulation is enabled)
        if highest_decision == Decision.ALLOW and self.config.simulation_enabled:
            sim_ok, sim_violations, diff, _ = self.sandbox.simulate_and_verify(intent)
            shadow_diff = diff
            if not sim_ok:
                violations.extend(sim_violations)
                highest_decision = Decision.DENY
                reason = f"Shadow state invariant violated: {sim_violations[0].message}"

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        result = VerificationResult(
            decision=highest_decision,
            intent_id=intent.intent_id,
            agent_id=intent.agent_id,
            session_id=intent.session_id,
            reason=reason,
            violations=violations,
            sanitized_arguments=sanitized_args,
            shadow_state_diff=shadow_diff,
            evaluation_latency_ms=round(elapsed_ms, 3),
            rules_evaluated_count=rules_evaluated,
            timestamp=time.time(),
        )

        # 7. Record into Cryptographic Merkle Ledger
        record = self.ledger.record_decision(intent, result)
        try:
            self.journal.persist_record(record)
        except Exception as e:
            logger.warning(f"Journal persistence error: {str(e)}")

        return result

    def execute_guarded(
        self,
        intent: ToolExecutionIntent,
        tool_callable: Callable[..., Any],
        session_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[VerificationResult, Optional[Any]]:
        """
        End-to-end verified execution wrapper.
        Verifies intent, invokes tool callable if allowed, verifies post-execution invariants,
        commits shadow state diff, and returns (result, output).
        """
        # Pre-execution verification
        ver_result = self.verify_intent(
            intent=intent,
            session_context=session_context,
            phase=PolicyPhase.PRE_EXECUTION,
        )

        if not ver_result.is_allowed:
            return ver_result, None

        # Execute the actual tool
        try:
            call_args = ver_result.sanitized_arguments or intent.arguments
            output = tool_callable(**call_args)
        except Exception as e:
            logger.error(f"Guarded tool execution raised exception: {str(e)}")
            raise e

        # Post-execution verification
        post_decision, post_violations, _, _ = self.policies.evaluate_intent(
            intent=intent,
            phase=PolicyPhase.POST_EXECUTION,
            session_context=session_context,
            result_payload=output,
        )

        if post_violations:
            ver_result.violations.extend(post_violations)
            ver_result.decision = post_decision
            ver_result.reason = f"Post-execution invariant breach: {post_violations[0].message}"

        # If everything allowed and shadow diff exists, commit shadow state
        if ver_result.is_allowed and ver_result.shadow_state_diff:
            _, _, _, simulated_state = self.sandbox.simulate_and_verify(intent)
            self.sandbox.commit_state(simulated_state)

        return ver_result, output

    def generate_proof(self, intent_id_or_index: Any) -> MerkleAuditProof:
        """Generates cryptographic inclusion proof for a ledger record."""
        return self.ledger.generate_proof(intent_id_or_index)

    def verify_proof(self, proof: MerkleAuditProof) -> bool:
        """Verifies inclusion proof statically."""
        return MerkleLedger.verify_proof_static(proof)
