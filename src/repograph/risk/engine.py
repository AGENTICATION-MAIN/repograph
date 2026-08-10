"""
Deterministic Risk Scoring Engine for Repograph.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from repograph.core.config import RepographConfig
from repograph.core.types import RiskFinding, ScanSummary, Severity
from repograph.graph.model import RepositoryGraph
from repograph.risk.heuristics import RiskHeuristics


class RiskEngine:
    """
    Deterministic Graph-Based Supply-Chain Risk Engine.
    Computes explainable risk scores without external network or LLM dependencies.
    """

    def __init__(self, config: Optional[RepographConfig] = None):
        self.config = config or RepographConfig()

    def analyze_graph(self, graph: RepositoryGraph, summary: ScanSummary) -> List[RiskFinding]:
        """
        Runs all risk rules, computes aggregate repository risk posture,
        and assigns node-level risk annotations.
        """
        findings = RiskHeuristics.evaluate_all(graph)

        # Compute summary counts by severity
        severity_counts = {s.value: 0 for s in Severity}
        for finding in findings:
            severity_counts[finding.severity.value] += 1

            # Assign risk score to affected nodes in the graph
            for node_id in finding.affected_nodes:
                node = graph.get_node(node_id)
                if node:
                    node.risk_score = max(node.risk_score, finding.risk_score)

        summary.findings_count_by_severity = severity_counts

        # Compute deterministic aggregate risk posture score [0.0 - 100.0]
        # Weighted formula: Critical (30 pts each), High (15 pts each), Medium (5 pts each), Low (1 pt each)
        raw_score = (
            severity_counts[Severity.CRITICAL.value] * 35.0
            + severity_counts[Severity.HIGH.value] * 18.0
            + severity_counts[Severity.MEDIUM.value] * 6.0
            + severity_counts[Severity.LOW.value] * 2.0
        )
        summary.aggregate_risk_score = min(100.0, raw_score)

        return findings
