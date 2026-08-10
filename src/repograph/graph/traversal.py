"""
Graph Traversal, Reachability, and Cycle Detection Algorithms for Repograph.
"""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from repograph.core.types import EdgeType, GraphEdge, GraphNode, NodeType
from repograph.graph.model import RepositoryGraph


class GraphTraversal:
    """Graph traversal algorithms: reachability, BFS/DFS paths, and cycle analysis."""

    def __init__(self, graph: RepositoryGraph):
        self.graph = graph

    def get_reachable_nodes(
        self,
        start_node_id: str,
        edge_types: Optional[Set[EdgeType]] = None,
        max_depth: int = 50,
    ) -> Set[str]:
        """Returns the set of all node IDs reachable from `start_node_id`."""
        visited: Set[str] = set()
        queue: deque[Tuple[str, int]] = deque([(start_node_id, 0)])

        while queue:
            curr_id, depth = queue.popleft()
            if curr_id in visited or depth > max_depth:
                continue
            visited.add(curr_id)

            for edge in self.graph.get_out_edges(curr_id):
                if edge_types is None or edge.edge_type in edge_types:
                    if edge.target_id not in visited:
                        queue.append((edge.target_id, depth + 1))

        return visited

    def find_shortest_path(
        self,
        start_node_id: str,
        target_node_id: str,
    ) -> Optional[List[GraphEdge]]:
        """Finds the shortest path of edges from start to target node using BFS."""
        if start_node_id == target_node_id:
            return []

        visited: Set[str] = {start_node_id}
        queue: deque[Tuple[str, List[GraphEdge]]] = deque([(start_node_id, [])])

        while queue:
            curr_id, path = queue.popleft()
            if curr_id == target_node_id:
                return path

            for edge in self.graph.get_out_edges(curr_id):
                if edge.target_id not in visited:
                    visited.add(edge.target_id)
                    queue.append((edge.target_id, path + [edge]))

        return None

    def detect_dependency_cycles(self) -> List[List[str]]:
        """Detects circular import and dependency cycles using Tarjan's / DFS cycle finding."""
        cycles: List[List[str]] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        import_edge_types = {EdgeType.IMPORTS, EdgeType.DEPENDS_ON}

        def dfs(node_id: str):
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            for edge in self.graph.get_out_edges(node_id):
                if edge.edge_type in import_edge_types:
                    target = edge.target_id
                    if target not in visited:
                        dfs(target)
                    elif target in rec_stack:
                        # Cycle found: extract cycle segment
                        idx = path.index(target)
                        cycle = list(path[idx:]) + [target]
                        cycles.append(cycle)

            path.pop()
            rec_stack.remove(node_id)

        for node in self.graph.list_nodes():
            if node.node_id not in visited:
                dfs(node.node_id)

        return cycles
