"""
Base Agent Framework Adapter Interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from aegis.core.kernel import AegisKernel
from aegis.core.types import VerificationResult


class BaseAgentAdapter(ABC):
    """Abstract base class for AI framework tool interceptors."""

    def __init__(self, kernel: AegisKernel):
        self.kernel = kernel

    @abstractmethod
    def intercept_and_verify(
        self,
        raw_tool_call: Any,
        agent_id: str,
        session_id: str,
        capability_token_id: Optional[str] = None,
        session_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[VerificationResult, Any]:
        """Intercepts raw tool call, runs AegisKernel verification, and formats response."""
        pass
