"""
REPOGRAPH — Production-Grade Software Supply-Chain Intelligence Engine.
"""

from repograph.core.config import RepographConfig
from repograph.core.exceptions import (
    FindingNotFoundError,
    GraphError,
    ParserError,
    RepographError,
    ScanError,
    UnsafePathError,
)
from repograph.core.types import (
    EdgeEvidence,
    EdgeType,
    GraphEdge,
    GraphNode,
    NodeType,
    RiskFinding,
    ScanSummary,
    Severity,
)
from repograph.graph.builder import GraphBuilder
from repograph.graph.export import GraphExporter
from repograph.graph.model import RepositoryGraph
from repograph.graph.traversal import GraphTraversal
from repograph.query.query_engine import QueryEngine
from repograph.risk.engine import RiskEngine

__version__ = "0.1.0"
__author__ = "Agentication-MAIN"

__all__ = [
    "GraphBuilder",
    "RepositoryGraph",
    "GraphTraversal",
    "GraphExporter",
    "RiskEngine",
    "QueryEngine",
    "NodeType",
    "EdgeType",
    "Severity",
    "EdgeEvidence",
    "GraphNode",
    "GraphEdge",
    "RiskFinding",
    "ScanSummary",
    "RepographConfig",
    "RepographError",
    "ScanError",
    "ParserError",
    "GraphError",
    "FindingNotFoundError",
    "UnsafePathError",
    "__version__",
]
