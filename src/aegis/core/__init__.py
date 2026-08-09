"""
AegisKernel Core Module.
"""

from aegis.core.types import (
    Decision,
    TaintLevel,
    PolicyPhase,
    Severity,
    TaintTag,
    CapabilityScope,
    ToolExecutionIntent,
    InvariantViolation,
    VerificationResult,
    MerkleAuditProof,
)
from aegis.core.exceptions import (
    AegisError,
    CapabilityError,
    CapabilityExpiredError,
    CapabilityScopeViolationError,
    PolicyEvaluationError,
    PolicySyntaxError,
    InvariantBreachError,
    TaintViolationError,
    MerkleIntegrityError,
    AdversarialAttackDetected,
    RateLimitExceededError,
    SandboxSimulationError,
)
from aegis.core.config import AegisConfig

__all__ = [
    "Decision",
    "TaintLevel",
    "PolicyPhase",
    "Severity",
    "TaintTag",
    "CapabilityScope",
    "ToolExecutionIntent",
    "InvariantViolation",
    "VerificationResult",
    "MerkleAuditProof",
    "AegisError",
    "CapabilityError",
    "CapabilityExpiredError",
    "CapabilityScopeViolationError",
    "PolicyEvaluationError",
    "PolicySyntaxError",
    "InvariantBreachError",
    "TaintViolationError",
    "MerkleIntegrityError",
    "AdversarialAttackDetected",
    "RateLimitExceededError",
    "SandboxSimulationError",
    "AegisConfig",
]
