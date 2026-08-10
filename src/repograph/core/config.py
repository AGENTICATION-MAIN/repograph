"""
Repograph Engine Configuration.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set


@dataclass
class RepographConfig:
    """Settings controlling scanner behavior, limits, and risk thresholds."""
    max_file_size_bytes: int = field(
        default_factory=lambda: int(os.getenv("REPOGRAPH_MAX_FILE_SIZE", str(5 * 1024 * 1024)))  # 5MB limit
    )
    max_depth: int = field(
        default_factory=lambda: int(os.getenv("REPOGRAPH_MAX_DEPTH", "30"))
    )
    follow_symlinks: bool = field(
        default_factory=lambda: os.getenv("REPOGRAPH_FOLLOW_SYMLINKS", "false").lower() in ("true", "1", "yes")
    )
    custom_ignore_patterns: List[str] = field(default_factory=list)
    enable_centrality_analysis: bool = True
    enable_cicd_analysis: bool = True
    enable_secret_heuristics: bool = True
    high_centrality_threshold: float = 0.15

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_file_size_bytes": self.max_file_size_bytes,
            "max_depth": self.max_depth,
            "follow_symlinks": self.follow_symlinks,
            "custom_ignore_patterns": self.custom_ignore_patterns,
            "enable_centrality_analysis": self.enable_centrality_analysis,
            "enable_cicd_analysis": self.enable_cicd_analysis,
            "enable_secret_heuristics": self.enable_secret_heuristics,
            "high_centrality_threshold": self.high_centrality_threshold,
        }
