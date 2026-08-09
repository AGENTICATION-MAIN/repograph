"""
AegisKernel Configuration Management.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AegisConfig:
    """Configuration settings for AegisKernel runtime."""
    environment: str = field(default_factory=lambda: os.getenv("AEGIS_ENV", "production"))
    log_level: str = field(default_factory=lambda: os.getenv("AEGIS_LOG_LEVEL", "INFO"))
    
    # Security & Cryptography
    hmac_secret_key: str = field(
        default_factory=lambda: os.getenv("AEGIS_SECRET_KEY", "aegis-default-development-secret-key-change-in-prod-32bytes")
    )
    strict_invariants: bool = field(
        default_factory=lambda: os.getenv("AEGIS_STRICT_INVARIANTS", "true").lower() in ("true", "1", "yes")
    )
    taint_tracking_enabled: bool = field(
        default_factory=lambda: os.getenv("AEGIS_TAINT_TRACKING", "true").lower() in ("true", "1", "yes")
    )
    
    # Server & API
    host: str = field(default_factory=lambda: os.getenv("AEGIS_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("AEGIS_PORT", "8000")))
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    
    # Storage & Persistence
    db_path: str = field(default_factory=lambda: os.getenv("AEGIS_DB_PATH", ":memory:"))
    ledger_storage_path: Optional[str] = field(default_factory=lambda: os.getenv("AEGIS_LEDGER_PATH", None))
    
    # Rate Limiting & Throttling
    default_rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv("AEGIS_DEFAULT_RATE_LIMIT", "120"))
    )
    
    # Simulation & Shadowing
    simulation_enabled: bool = field(
        default_factory=lambda: os.getenv("AEGIS_SIMULATION_ENABLED", "true").lower() in ("true", "1", "yes")
    )
    max_shadow_memory_mb: int = field(
        default_factory=lambda: int(os.getenv("AEGIS_MAX_SHADOW_MB", "64"))
    )

    def to_dict(self) -> Dict[str, Any]:
        """Safe representation without exposing secret keys."""
        return {
            "environment": self.environment,
            "log_level": self.log_level,
            "strict_invariants": self.strict_invariants,
            "taint_tracking_enabled": self.taint_tracking_enabled,
            "host": self.host,
            "port": self.port,
            "db_path": self.db_path,
            "default_rate_limit_per_minute": self.default_rate_limit_per_minute,
            "simulation_enabled": self.simulation_enabled,
            "max_shadow_memory_mb": self.max_shadow_memory_mb,
            "secret_configured": bool(self.hmac_secret_key and len(self.hmac_secret_key) >= 16),
        }
