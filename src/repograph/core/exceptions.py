"""
Repograph Exceptions and Error Handling.
"""

from typing import Any, Dict, Optional


class RepographError(Exception):
    """Base exception for all Repograph operational errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ScanError(RepographError):
    """Raised when repository directory traversal fails."""
    pass


class ParserError(RepographError):
    """Raised when parsing a source manifest, workflow, or config file fails."""
    pass


class GraphError(RepographError):
    """Raised when graph invariants or node/edge integrity checks fail."""
    pass


class FindingNotFoundError(RepographError):
    """Raised when a specific finding ID is not found during explanation queries."""
    pass


class UnsafePathError(RepographError):
    """Raised when a path traversal attempt or malicious symlink is detected."""
    pass
