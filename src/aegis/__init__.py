"""
AegisKernel: High-Assurance Runtime & Deterministic Verification Engine for Autonomous AI Agents.
"""

from aegis.core.config import AegisConfig
from aegis.core.exceptions import (
    AegisError,
    CapabilityError,
    CapabilityExpiredError,
    CapabilityScopeViolationError,
    InvariantBreachError,
    MerkleIntegrityError,
    PolicyEvaluationError,
    PolicySyntaxError,
    RateLimitExceededError,
    SandboxSimulationError,
    TaintViolationError,
)
from aegis.core.kernel import AegisKernel
from aegis.core.types import (
    CapabilityScope,
    Decision,
    InvariantViolation,
    MerkleAuditProof,
    PolicyPhase,
    Severity,
    TaintLevel,
    TaintTag,
    ToolExecutionIntent,
    VerificationResult,
)
from aegis.policy.parser import PolicyParser, PolicyRule

__version__ = "0.1.0"
__author__ = "Agentication-MAIN"

__all__ = [
    "AegisKernel",
    "AegisConfig",
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
    "PolicyParser",
    "PolicyRule",
    "AegisError",
    "CapabilityError",
    "CapabilityExpiredError",
    "CapabilityScopeViolationError",
    "InvariantBreachError",
    "MerkleIntegrityError",
    "PolicyEvaluationError",
    "PolicySyntaxError",
    "RateLimitExceededError",
    "SandboxSimulationError",
    "TaintViolationError",
    "__version__",
]
