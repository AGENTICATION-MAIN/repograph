"""
Repograph Core Types and Data Models.

Defines the fundamental graph primitives, node/edge taxonomies, evidence metadata,
and risk finding structures for static repository supply-chain intelligence.
"""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union


class NodeType(str, enum.Enum):
    """Taxonomy of entities discovered in the repository graph."""
    REPOSITORY = "Repository"
    FILE = "File"
    DIRECTORY = "Directory"
    MODULE = "Module"
    PACKAGE = "Package"
    DEPENDENCY = "Dependency"
    WORKFLOW = "Workflow"
    CONFIGURATION = "Configuration"
    SERVICE = "Service"


class EdgeType(str, enum.Enum):
    """Taxonomy of relationships connecting entities in the repository graph."""
    CONTAINS = "CONTAINS"          # Parent container -> Child element (e.g. Repo -> Dir, Dir -> File)
    IMPORTS = "IMPORTS"            # Source file -> Imported module/package
    DEPENDS_ON = "DEPENDS_ON"      # Manifest/Module -> Direct/transitive dependency
    EXECUTES = "EXECUTES"          # CI/CD Workflow -> Step/Action/Script
    CONFIGURES = "CONFIGURES"      # Configuration file -> Service/Environment/Runtime
    CALLS = "CALLS"                # Function/Endpoint invocation
    EXPOSES = "EXPOSES"            # Service -> Port/API endpoint/Route
    TRUSTS = "TRUSTS"              # Workflow/App -> Secret/External action/Auth provider


class Severity(str, enum.Enum):
    """Deterministic risk severity ratings."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

    @property
    def score_multiplier(self) -> float:
        if self == Severity.CRITICAL:
            return 1.0
        elif self == Severity.HIGH:
            return 0.75
        elif self == Severity.MEDIUM:
            return 0.50
        elif self == Severity.LOW:
            return 0.25
        return 0.10


@dataclass
class EdgeEvidence:
    """
    Traceable evidence attached to every graph relationship edge.
    Guarantees explainability and verifiable provenance for all findings.
    """
    source_file: str
    line_number: Optional[int] = None
    extraction_method: str = "static_parser"  # e.g. "ast_import", "manifest_parser", "workflow_yaml"
    confidence_score: float = 1.0             # Range: 0.0 to 1.0
    snippet: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_file": self.source_file,
            "line_number": self.line_number,
            "extraction_method": self.extraction_method,
            "confidence_score": self.confidence_score,
            "snippet": self.snippet,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EdgeEvidence:
        return cls(
            source_file=data["source_file"],
            line_number=data.get("line_number"),
            extraction_method=data.get("extraction_method", "static_parser"),
            confidence_score=float(data.get("confidence_score", 1.0)),
            snippet=data.get("snippet"),
        )


@dataclass
class GraphNode:
    """A typed vertex in the repository intelligence graph."""
    node_id: str
    node_type: NodeType
    name: str
    path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    centrality_score: float = 0.0
    risk_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "name": self.name,
            "path": self.path,
            "metadata": self.metadata,
            "centrality_score": round(self.centrality_score, 4),
            "risk_score": round(self.risk_score, 2),
        }


@dataclass
class GraphEdge:
    """A directed, typed, evidence-backed relationship edge."""
    source_id: str
    target_id: str
    edge_type: EdgeType
    evidence: EdgeEvidence
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def edge_id(self) -> str:
        return f"{self.source_id}->{self.edge_type.value}->{self.target_id}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "evidence": self.evidence.to_dict(),
            "metadata": self.metadata,
        }


@dataclass
class RiskFinding:
    """A deterministic supply-chain or architectural risk finding."""
    finding_id: str
    rule_id: str
    title: str
    severity: Severity
    risk_score: float                  # Scale 0.0 - 100.0
    explanation: str
    evidence: List[EdgeEvidence] = field(default_factory=list)
    affected_nodes: List[str] = field(default_factory=list)
    remediation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "rule_id": self.rule_id,
            "title": self.title,
            "severity": self.severity.value,
            "risk_score": round(self.risk_score, 2),
            "explanation": self.explanation,
            "evidence": [e.to_dict() for e in self.evidence],
            "affected_nodes": self.affected_nodes,
            "remediation": self.remediation,
            "metadata": self.metadata,
        }


@dataclass
class ScanSummary:
    """Aggregate overview of repository scan metrics."""
    repository_path: str
    total_files: int = 0
    total_directories: int = 0
    total_dependencies: int = 0
    total_workflows: int = 0
    total_configs: int = 0
    total_nodes: int = 0
    total_edges: int = 0
    languages: Dict[str, int] = field(default_factory=dict)
    ecosystems: Set[str] = field(default_factory=set)
    findings_count_by_severity: Dict[str, int] = field(default_factory=dict)
    aggregate_risk_score: float = 0.0
    scan_duration_seconds: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repository_path": self.repository_path,
            "total_files": self.total_files,
            "total_directories": self.total_directories,
            "total_dependencies": self.total_dependencies,
            "total_workflows": self.total_workflows,
            "total_configs": self.total_configs,
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "languages": self.languages,
            "ecosystems": sorted(list(self.ecosystems)),
            "findings_count_by_severity": self.findings_count_by_severity,
            "aggregate_risk_score": round(self.aggregate_risk_score, 2),
            "scan_duration_seconds": round(self.scan_duration_seconds, 4),
            "timestamp": self.timestamp,
        }
