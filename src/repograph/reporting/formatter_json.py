"""
JSON Formatter for Repograph.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from repograph.core.types import RiskFinding, ScanSummary
from repograph.graph.model import RepositoryGraph


class JsonFormatter:
    """Formats full scan results as machine-readable JSON."""

    @staticmethod
    def format(
        summary: ScanSummary,
        graph: RepositoryGraph,
        findings: List[RiskFinding],
        indent: int = 2,
    ) -> str:
        data = {
            "schema_version": "1.0.0",
            "summary": summary.to_dict(),
            "findings": [f.to_dict() for f in findings],
            "graph": graph.to_dict(),
        }
        return json.dumps(data, indent=indent)
