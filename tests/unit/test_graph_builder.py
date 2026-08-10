"""
Unit tests for GraphBuilder and Evidence Tracking.
"""

import pytest
from repograph.core.types import EdgeType, NodeType


def test_graph_builder_structure(sample_graph):
    graph, summary = sample_graph

    assert graph.node_count > 10
    assert graph.edge_count > 10

    assert summary.total_files > 0
    assert summary.total_dependencies >= 8
    assert summary.total_workflows >= 1
    assert "pypi" in summary.ecosystems
    assert "npm" in summary.ecosystems
    assert "golang" in summary.ecosystems

    # Verify edge evidence is attached to every single edge
    for edge in graph.list_edges():
        assert edge.evidence is not None
        assert edge.evidence.source_file != ""
        assert edge.evidence.confidence_score > 0.0
