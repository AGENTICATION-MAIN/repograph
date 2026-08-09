"""
Aegis Security, Threat Detection, and Rate Limiting Subsystem.
"""

from aegis.security.adversarial import AdversarialDetector, ThreatPattern, KNOWN_THREAT_PATTERNS
from aegis.security.sanitizers import (
    sanitize_html,
    mask_pii,
    sanitize_sql_identifier,
    sanitize_shell_arg,
    SanitizerRegistry,
)
from aegis.security.rate_limiter import SlidingWindowRateLimiter

__all__ = [
    "AdversarialDetector",
    "ThreatPattern",
    "KNOWN_THREAT_PATTERNS",
    "sanitize_html",
    "mask_pii",
    "sanitize_sql_identifier",
    "sanitize_shell_arg",
    "SanitizerRegistry",
    "SlidingWindowRateLimiter",
]
