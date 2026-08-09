"""
Pactum Kernel Runtime Configuration.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PactumConfig:
    """Configuration options for Pactum bartering runtime."""
    environment: str = field(default_factory=lambda: os.getenv("PACTUM_ENV", "production"))
    log_level: str = field(default_factory=lambda: os.getenv("PACTUM_LOG_LEVEL", "INFO"))
    
    # Cryptographic Security
    hmac_secret_key: str = field(
        default_factory=lambda: os.getenv("PACTUM_SECRET_KEY", "pactum-secret-key-32bytes-for-coasian-barter-kernel")
    )
    
    # Server & API
    host: str = field(default_factory=lambda: os.getenv("PACTUM_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PACTUM_PORT", "8000")))
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    
    # Bargaining & Market Parameters
    nash_convergence_tolerance: float = field(
        default_factory=lambda: float(os.getenv("PACTUM_NASH_TOLERANCE", "1e-6"))
    )
    max_bargaining_iterations: int = field(
        default_factory=lambda: int(os.getenv("PACTUM_MAX_ITERATIONS", "100"))
    )
    default_lease_ttl_seconds: float = field(
        default_factory=lambda: float(os.getenv("PACTUM_LEASE_TTL", "60.0"))
    )
    enforce_atomic_escrow: bool = field(
        default_factory=lambda: os.getenv("PACTUM_ATOMIC_ESCROW", "true").lower() in ("true", "1", "yes")
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "environment": self.environment,
            "log_level": self.log_level,
            "host": self.host,
            "port": self.port,
            "nash_convergence_tolerance": self.nash_convergence_tolerance,
            "max_bargaining_iterations": self.max_bargaining_iterations,
            "default_lease_ttl_seconds": self.default_lease_ttl_seconds,
            "enforce_atomic_escrow": self.enforce_atomic_escrow,
        }
