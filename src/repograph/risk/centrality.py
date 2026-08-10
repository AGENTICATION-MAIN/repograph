"""
Graph Centrality and Criticality Metrics for Repograph.
"""

from __future__ import annotations

from typing import Dict, List, Set

from repograph.core.types import NodeType
from repograph.graph.model import RepositoryGraph


class CentralityAnalyzer:
    """
    Computes degree centrality, in-degree (dependents count), and PageRank-style
    influence scores over graph nodes.
    """

    def __init__(self, graph: RepositoryGraph):
        self.graph = graph

    def compute_degree_centrality(self) -> Dict[str, float]:
        """Calculates normalized degree centrality for all nodes."""
        n = self.graph.node_count
        if n <= 1:
            return {node.node_id: 0.0 for node in self.graph.list_nodes()}

        centrality: Dict[str, float] = {}
        for node in self.graph.list_nodes():
            in_edges = len(self.graph.get_in_edges(node.node_id))
            out_edges = len(self.graph.get_out_edges(node.node_id))
            deg = in_edges + out_edges
            score = deg / (n - 1)
            centrality[node.node_id] = score
            node.centrality_score = score

        return centrality

    def compute_in_degree_dependents(self) -> Dict[str, int]:
        """Returns direct incoming dependent counts for all nodes."""
        return {
            node.node_id: len(self.graph.get_in_edges(node.node_id))
            for node in self.graph.list_nodes()
        }
