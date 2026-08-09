"""
Pactum Domain Exceptions.
"""

from typing import Any, Dict, List, Optional


class PactumError(Exception):
    """Base exception for all Pactum errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}


class BargainingError(PactumError):
    """Raised when bilateral negotiation or equilibrium calculation fails."""
    pass


class NoMutuallyBeneficialTradeError(BargainingError):
    """Raised when two utility curves have no overlapping surplus (empty Edgeworth contract curve)."""
    pass


class InsufficientCapabilityError(PactumError):
    """Raised when a service lacks available capability tokens to fulfill an offer."""
    pass


class EscrowSettlementError(PactumError):
    """Raised when atomic capability lease swap fails or is rejected."""
    pass


class LeaseExpiredError(PactumError):
    """Raised when attempting to consume an expired capability lease."""
    pass


class LeaseQuotaExceededError(PactumError):
    """Raised when a lease has exceeded its allocated consumption quota."""
    pass


class CounterpartyDefaultError(PactumError):
    """Raised when a trading counterparty fails to honor an atomic lease agreement."""
    pass
