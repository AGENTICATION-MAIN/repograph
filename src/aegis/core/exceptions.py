"""
AegisKernel Domain Exceptions.
"""

from typing import Any, Dict, List, Optional


class AegisError(Exception):
    """Base exception for all AegisKernel errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}


class CapabilityError(AegisError):
    """Raised when capability token validation fails."""
    pass


class CapabilityExpiredError(CapabilityError):
    """Raised when a capability token has exceeded its TTL."""
    pass


class CapabilityScopeViolationError(CapabilityError):
    """Raised when an operation exceeds allowed capability scope."""
    pass


class PolicyEvaluationError(AegisError):
    """Raised when policy compilation or evaluation fails."""
    pass


class PolicySyntaxError(PolicyEvaluationError):
    """Raised when policy DSL contains syntax errors."""
    pass


class InvariantBreachError(AegisError):
    """Raised when an invariant condition is violated in strict mode."""
    def __init__(self, message: str, violations: Optional[List[Any]] = None):
        super().__init__(message, {"violations": violations or []})
        self.violations = violations or []


class TaintViolationError(AegisError):
    """Raised when untrusted tainted data flows into a protected sink."""
    pass


class MerkleIntegrityError(AegisError):
    """Raised when the cryptographic audit ledger fails mathematical verification."""
    pass


class AdversarialAttackDetected(AegisError):
    """Raised when an active prompt injection or adversarial bypass is detected."""
    pass


class RateLimitExceededError(AegisError):
    """Raised when an agent exceeds execution rate limits."""
    pass


class SandboxSimulationError(AegisError):
    """Raised when pre-flight shadow state simulation fails."""
    pass
