"""
Blast Radius Estimation for Repograph.
"""

from __future__ import annotations

from typing import Dict, Set

from repograph.core.types import EdgeType
from repograph.graph.model import RepositoryGraph
from repograph.graph.traversal import GraphTraversal


class BlastRadiusEstimator:
    """Estimates the downstream impact and reachability footprint if a node is compromised."""

    def __init__(self, graph: RepositoryGraph):
        self.graph = graph
        self.traversal = GraphTraversal(graph)

    def estimate_blast_radius(self, node_id: str) -> Dict[str, Any]:
        """Computes all reachable downstream nodes and percentage of total repo affected."""
        # For dependencies or modules, blast radius is who depends on it (reverse reachability)
        visited: Set[str] = set()
        queue = [node_id]

        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)

            # Look at incoming edges (who imports/depends on this)
            for in_edge in self.graph.get_in_edges(curr):
                if in_edge.source_id not in visited:
                    queue.append(in_edge.source_id)

        total_nodes = max(1, self.graph.node_count)
        impacted_count = len(visited)
        ratio = impacted_count / total_nodes

        return {
            "node_id": node_id,
            "impacted_node_count": impacted_count,
            "impact_ratio": round(ratio, 4),
            "impacted_nodes": list(visited),
        }
