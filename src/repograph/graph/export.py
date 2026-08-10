"""
Graph Exporters for Repograph (DOT / Mermaid / JSON).
"""

from __future__ import annotations

import json
from typing import Any, Dict

from repograph.graph.model import RepositoryGraph


class GraphExporter:
    """Serializes repository graph to various industry standard diagram and data formats."""

    @staticmethod
    def to_json(graph: RepositoryGraph, indent: int = 2) -> str:
        return json.dumps(graph.to_dict(), indent=indent)

    @staticmethod
    def to_mermaid(graph: RepositoryGraph, max_nodes: int = 150) -> str:
        """Generates Mermaid.js diagram flowchart syntax."""
        lines = ["graph TD"]
        nodes = graph.list_nodes()[:max_nodes]
        node_ids = {n.node_id for n in nodes}

        # Node declarations with stylized shapes
        for node in nodes:
            safe_id = node.node_id.replace(":", "_").replace("/", "_").replace(".", "_").replace("-", "_")
            label = node.name.replace('"', '\\"')
            if node.node_type.value == "Repository":
                lines.append(f'  {safe_id}[("{label}")]')
            elif node.node_type.value == "Dependency":
                lines.append(f'  {safe_id}(["{label}"])')
            elif node.node_type.value == "Workflow":
                lines.append(f'  {safe_id}{{"{label}"}}')
            else:
                lines.append(f'  {safe_id}["{label}"]')

        # Edges
        for edge in graph.list_edges():
            if edge.source_id in node_ids and edge.target_id in node_ids:
                s_id = edge.source_id.replace(":", "_").replace("/", "_").replace(".", "_").replace("-", "_")
                t_id = edge.target_id.replace(":", "_").replace("/", "_").replace(".", "_").replace("-", "_")
                lines.append(f'  {s_id} -->|{edge.edge_type.value}| {t_id}')

        return "\n".join(lines)

    @staticmethod
    def to_dot(graph: RepositoryGraph) -> str:
        """Generates Graphviz DOT syntax."""
        lines = ['digraph RepositoryGraph {', '  rankdir=LR;', '  node [shape=box, fontname="Helvetica"];']
        for node in graph.list_nodes():
            safe_id = f'"{node.node_id}"'
            lines.append(f'  {safe_id} [label="{node.name}\\n({node.node_type.value})"];')

        for edge in graph.list_edges():
            s_id = f'"{edge.source_id}"'
            t_id = f'"{edge.target_id}"'
            lines.append(f'  {s_id} -> {t_id} [label="{edge.edge_type.value}"];')

        lines.append('}')
        return "\n".join(lines)
