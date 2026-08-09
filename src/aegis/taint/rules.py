"""
Taint Sink and Propagation Rule Definitions for AegisKernel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from aegis.core.types import TaintLevel


@dataclass
class TaintSinkRule:
    """
    Specifies taint restrictions for a sensitive tool parameter (Sink).
    """
    tool_name: str
    parameter_name: str
    max_allowed_taint: TaintLevel
    requires_sanitization: bool = True
    allowed_sanitizers: Set[str] = field(default_factory=set)
    description: str = ""

    def is_violated(self, current_taint: TaintLevel, is_sanitized: bool, sanitizer: Optional[str]) -> bool:
        """Determines if providing data with given taint violates this sink rule."""
        if current_taint.value > self.max_allowed_taint.value:
            if not is_sanitized:
                return True
            if self.allowed_sanitizers and (sanitizer not in self.allowed_sanitizers):
                return True
        return False


# Standard enterprise sink policy definitions
DEFAULT_SINK_RULES: List[TaintSinkRule] = [
    TaintSinkRule(
        tool_name="execute_sql",
        parameter_name="query",
        max_allowed_taint=TaintLevel.AUTHENTICATED_USER,
        requires_sanitization=True,
        allowed_sanitizers={"parameterized_query_sanitizer", "sql_ast_validator"},
        description="Raw SQL queries cannot contain untrusted external data without AST validation.",
    ),
    TaintSinkRule(
        tool_name="execute_bash",
        parameter_name="command",
        max_allowed_taint=TaintLevel.SYSTEM,
        requires_sanitization=True,
        allowed_sanitizers={"shell_escape_sanitizer"},
        description="Shell execution requires trusted system-origin data only.",
    ),
    TaintSinkRule(
        tool_name="transfer_funds",
        parameter_name="recipient_account",
        max_allowed_taint=TaintLevel.AUTHENTICATED_USER,
        requires_sanitization=True,
        allowed_sanitizers={"kyc_account_verifier"},
        description="Fund transfer recipient must originate from authenticated user and verified account.",
    ),
    TaintSinkRule(
        tool_name="transfer_funds",
        parameter_name="amount",
        max_allowed_taint=TaintLevel.AUTHENTICATED_USER,
        requires_sanitization=False,
        description="Fund transfer amount must not originate from unauthenticated external scraping.",
    ),
    TaintSinkRule(
        tool_name="send_external_email",
        parameter_name="recipient",
        max_allowed_taint=TaintLevel.AUTHENTICATED_USER,
        requires_sanitization=False,
        description="Email recipient addresses must originate from verified user records.",
    ),
]
