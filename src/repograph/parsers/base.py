"""
Base Parser Interface for Repograph.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from repograph.core.types import EdgeEvidence, GraphEdge, GraphNode


class BaseParser(ABC):
    """Abstract base class for all manifest, source, configuration, and CI/CD parsers."""

    @abstractmethod
    def can_parse(self, file_path: Path, relative_path: str) -> bool:
        """Determines if this parser handles the given file."""
        pass

    @abstractmethod
    def parse(
        self,
        file_path: Path,
        relative_path: str,
        content: str,
    ) -> List[Tuple[GraphNode, GraphEdge]]:
        """
        Parses file content and extracts discovered nodes and connected relationship edges.
        """
        pass
