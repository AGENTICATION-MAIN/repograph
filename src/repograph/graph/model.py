"""
Repository Intelligence Graph Model for Repograph.

Provides an in-memory graph representation with indexed node lookups,
multi-typed adjacency lists, and evidence preservation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from repograph.core.types import EdgeType, GraphEdge, GraphNode, NodeType


class RepositoryGraph:
    """
    Directed Multi-Edge Graph representing all repository assets, imports,
    dependencies, configurations, and CI/CD pipelines.
    """

    def __init__(self, root_name: str = "repository"):
        self.root_name = root_name
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: Dict[str, GraphEdge] = {}
        self._out_edges: Dict[str, List[str]] = {}  # node_id -> [edge_id]
        self._in_edges: Dict[str, List[str]] = {}   # node_id -> [edge_id]
        self._nodes_by_type: Dict[NodeType, Set[str]] = {t: set() for t in NodeType}

    def add_node(self, node: GraphNode) -> GraphNode:
        """Adds or updates a node in the graph."""
        if node.node_id not in self._nodes:
            self._nodes[node.node_id] = node
            self._out_edges[node.node_id] = []
            self._in_edges[node.node_id] = []
            self._nodes_by_type[node.node_type].add(node.node_id)
        else:
            # Merge metadata if node exists
            existing = self._nodes[node.node_id]
            existing.metadata.update(node.metadata)
            if node.path and not existing.path:
                existing.path = node.path
        return self._nodes[node.node_id]

    def add_edge(self, edge: GraphEdge) -> Optional[GraphEdge]:
        """Adds an evidence-backed directed relationship edge."""
        # Ensure source and target nodes exist (or create placeholders)
        if edge.source_id not in self._nodes:
            self.add_node(GraphNode(node_id=edge.source_id, node_type=NodeType.FILE, name=edge.source_id))
        if edge.target_id not in self._nodes:
            self.add_node(GraphNode(node_id=edge.target_id, node_type=NodeType.MODULE, name=edge.target_id))

        edge_key = edge.edge_id
        if edge_key not in self._edges:
            self._edges[edge_key] = edge
            self._out_edges[edge.source_id].append(edge_key)
            self._in_edges[edge.target_id].append(edge_key)
            return edge
        return self._edges[edge_key]

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def get_edge(self, edge_id: str) -> Optional[GraphEdge]:
        return self._edges.get(edge_id)

    def list_nodes(self, node_type: Optional[NodeType] = None) -> List[GraphNode]:
        if node_type:
            ids = self._nodes_by_type.get(node_type, set())
            return [self._nodes[nid] for nid in ids if nid in self._nodes]
        return list(self._nodes.values())

    def list_edges(self, edge_type: Optional[EdgeType] = None) -> List[GraphEdge]:
        if edge_type:
            return [e for e in self._edges.values() if e.edge_type == edge_type]
        return list(self._edges.values())

    def get_out_edges(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[GraphEdge]:
        edge_ids = self._out_edges.get(node_id, [])
        edges = [self._edges[eid] for eid in edge_ids if eid in self._edges]
        if edge_type:
            edges = [e for e in edges if e.edge_type == edge_type]
        return edges

    def get_in_edges(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[GraphEdge]:
        edge_ids = self._in_edges.get(node_id, [])
        edges = [self._edges[eid] for eid in edge_ids if eid in self._edges]
        if edge_type:
            edges = [e for e in edges if e.edge_type == edge_type]
        return edges

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_name": self.root_name,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for e in self._edges.values()],
        }
