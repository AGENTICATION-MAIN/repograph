"""
Query Engine for Repograph Intelligence Graph.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from repograph.core.exceptions import FindingNotFoundError
from repograph.core.types import EdgeType, GraphEdge, GraphNode, NodeType, RiskFinding
from repograph.graph.model import RepositoryGraph
from repograph.graph.traversal import GraphTraversal


class QueryEngine:
    """Provides deterministic graph queries and forensic finding explanations."""

    def __init__(self, graph: RepositoryGraph, findings: Optional[List[RiskFinding]] = None):
        self.graph = graph
        self.findings = {f.finding_id: f for f in (findings or [])}
        self.traversal = GraphTraversal(graph)

    def explain_finding(self, finding_id: str) -> Dict[str, Any]:
        """Deep forensic inspection of a risk finding with full evidence chain and affected paths."""
        if finding_id not in self.findings:
            raise FindingNotFoundError(f"Risk finding with ID '{finding_id}' not found.")

        finding = self.findings[finding_id]
        affected_nodes_info = []
        for nid in finding.affected_nodes:
            node = self.graph.get_node(nid)
            if node:
                in_edges = [e.to_dict() for e in self.graph.get_in_edges(nid)]
                out_edges = [e.to_dict() for e in self.graph.get_out_edges(nid)]
                affected_nodes_info.append({
                    "node": node.to_dict(),
                    "incoming_relationships": in_edges,
                    "outgoing_relationships": out_edges,
                })

        return {
            "finding": finding.to_dict(),
            "affected_topology": affected_nodes_info,
            "evidence_count": len(finding.evidence),
        }

    def query_dependents(self, package_or_module_name: str) -> List[Dict[str, Any]]:
        """Finds all files in the repository that directly or transitively depend on a package."""
        results = []
        for node in self.graph.list_nodes():
            if package_or_module_name.lower() in node.name.lower():
                in_edges = self.graph.get_in_edges(node.node_id)
                results.append({
                    "target_node": node.to_dict(),
                    "direct_dependents": [self.graph.get_node(e.source_id).to_dict() for e in in_edges if self.graph.get_node(e.source_id)],
                    "total_direct_dependents": len(in_edges),
                })
        return results

    def query_cicd_trust_boundary(self) -> List[Dict[str, Any]]:
        """Returns all workflows and the external dependencies or secrets they trust."""
        results = []
        for wf_node in self.graph.list_nodes(NodeType.WORKFLOW):
            trust_edges = self.graph.get_out_edges(wf_node.node_id, EdgeType.TRUSTS)
            exec_edges = self.graph.get_out_edges(wf_node.node_id, EdgeType.EXECUTES)
            results.append({
                "workflow": wf_node.to_dict(),
                "trusted_entities": [self.graph.get_node(e.target_id).to_dict() for e in trust_edges if self.graph.get_node(e.target_id)],
                "executed_actions": [self.graph.get_node(e.target_id).to_dict() for e in exec_edges if self.graph.get_node(e.target_id)],
            })
        return results
