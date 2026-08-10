"""
Integration test: End-to-End scan of fixture repository.
"""

from pathlib import Path
import pytest
from repograph.graph.builder import GraphBuilder
from repograph.risk.engine import RiskEngine


def test_full_repository_scan_pipeline(sample_repo_path):
    builder = GraphBuilder(sample_repo_path)
    graph, summary = builder.build_graph()

    risk_engine = RiskEngine()
    findings = risk_engine.analyze_graph(graph, summary)

    assert summary.total_files >= 10
    assert summary.total_dependencies >= 8
    assert summary.total_workflows >= 1
    assert len(findings) >= 5

    # Check that node risk scores were updated on the graph
    high_risk_nodes = [n for n in graph.list_nodes() if n.risk_score > 0.0]
    assert len(high_risk_nodes) >= 5
