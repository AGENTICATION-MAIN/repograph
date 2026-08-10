"""
Deterministic Supply-Chain and Architecture Risk Rules for Repograph.
"""

from __future__ import annotations

import hashlib
from typing import List, Optional

from repograph.core.types import (
    EdgeEvidence,
    EdgeType,
    GraphNode,
    NodeType,
    RiskFinding,
    Severity,
)
from repograph.graph.model import RepositoryGraph
from repograph.graph.traversal import GraphTraversal
from repograph.risk.blast_radius import BlastRadiusEstimator
from repograph.risk.centrality import CentralityAnalyzer


def deterministic_finding_id(rule_id: str, seed: str) -> str:
    """Generates a stable, reproducible finding ID based on rule and entity names."""
    h = hashlib.sha256(f"{rule_id}:{seed}".encode("utf-8")).hexdigest()[:8].upper()
    return f"FIND-{h}"


class RiskHeuristics:
    """Evaluates graph topology against deterministic software supply-chain risk rules."""

    @staticmethod
    def evaluate_all(graph: RepositoryGraph) -> List[RiskFinding]:
        findings: List[RiskFinding] = []

        centrality_analyzer = CentralityAnalyzer(graph)
        centrality_scores = centrality_analyzer.compute_degree_centrality()
        blast_estimator = BlastRadiusEstimator(graph)
        traversal = GraphTraversal(graph)

        # Rule 1: CI/CD Secret Exposure on pull_request_target
        for wf_node in graph.list_nodes(NodeType.WORKFLOW):
            if wf_node.metadata.get("is_pull_request_target"):
                trust_edges = graph.get_out_edges(wf_node.node_id, EdgeType.TRUSTS)
                for edge in trust_edges:
                    target_node = graph.get_node(edge.target_id)
                    if target_node and target_node.metadata.get("is_github_secret"):
                        finding_id = deterministic_finding_id(
                            "RULE_CICD_PULL_REQUEST_TARGET_SECRET_EXPOSURE",
                            f"{wf_node.node_id}:{target_node.node_id}",
                        )
                        findings.append(RiskFinding(
                            finding_id=finding_id,
                            rule_id="RULE_CICD_PULL_REQUEST_TARGET_SECRET_EXPOSURE",
                            title=f"CI/CD Secret Access on Untrusted pull_request_target Trigger in {wf_node.name}",
                            severity=Severity.CRITICAL,
                            risk_score=95.0,
                            explanation=(
                                f"Workflow '{wf_node.name}' ({wf_node.path}) triggers on 'pull_request_target' "
                                f"and accesses repository secret '{target_node.name}'. "
                                "This allows pull requests from untrusted external forks to execute malicious code "
                                "with access to privileged repository secrets."
                            ),
                            evidence=[edge.evidence],
                            affected_nodes=[wf_node.node_id, target_node.node_id],
                            remediation=(
                                "Use 'pull_request' instead of 'pull_request_target', or do not grant secret access "
                                "until external code has been verified and merged."
                            ),
                        ))

        # Rule 2: Unpinned Third-Party GitHub Actions
        for action_node in graph.list_nodes(NodeType.DEPENDENCY):
            if action_node.metadata.get("ecosystem") == "github-actions":
                if action_node.metadata.get("is_third_party") and not action_node.metadata.get("is_pinned_sha"):
                    exec_edges = graph.get_in_edges(action_node.node_id, EdgeType.EXECUTES)
                    evidence_list = [e.evidence for e in exec_edges]
                    finding_id = deterministic_finding_id("RULE_UNPINNED_THIRD_PARTY_ACTION", action_node.node_id)
                    findings.append(RiskFinding(
                        finding_id=finding_id,
                        rule_id="RULE_UNPINNED_THIRD_PARTY_ACTION",
                        title=f"Unpinned 3rd-Party GitHub Action: {action_node.name}",
                        severity=Severity.HIGH,
                        risk_score=75.0,
                        explanation=(
                            f"Third-party action '{action_node.name}' uses a mutable tag rather than an immutable commit SHA. "
                            "If the action maintainer account is compromised, malicious code could be silently injected "
                            "into your CI/CD pipeline."
                        ),
                        evidence=evidence_list,
                        affected_nodes=[action_node.node_id],
                        remediation=f"Pin '{action_node.name}' to a full 40-character commit SHA (e.g. action@<commit-sha>).",
                    ))

        # Rule 3: Unpinned Docker Base Images (e.g. :latest or untagged)
        for docker_node in graph.list_nodes(NodeType.DEPENDENCY):
            if docker_node.metadata.get("ecosystem") == "docker" and docker_node.metadata.get("is_unpinned_base"):
                dep_edges = graph.get_in_edges(docker_node.node_id, EdgeType.DEPENDS_ON)
                finding_id = deterministic_finding_id("RULE_UNPINNED_DOCKER_BASE", docker_node.node_id)
                findings.append(RiskFinding(
                    finding_id=finding_id,
                    rule_id="RULE_UNPINNED_DOCKER_BASE",
                    title=f"Unpinned Docker Base Image: {docker_node.name}",
                    severity=Severity.MEDIUM,
                    risk_score=50.0,
                    explanation=(
                        f"Docker base image '{docker_node.name}' uses ':latest' or lacks an explicit version tag. "
                        "Upstream image changes can lead to non-reproducible builds and unexpected supply-chain updates."
                    ),
                    evidence=[e.evidence for e in dep_edges],
                    affected_nodes=[docker_node.node_id],
                    remediation=f"Pin '{docker_node.name}' to a specific version or digest hash (e.g. python:3.12-slim).",
                ))

        # Rule 4: Plaintext Secret in Config / Environment File
        for conf_node in graph.list_nodes(NodeType.CONFIGURATION):
            if conf_node.metadata.get("is_plaintext_secret"):
                conf_edges = graph.get_in_edges(conf_node.node_id, EdgeType.CONFIGURES)
                finding_id = deterministic_finding_id("RULE_PLAINTEXT_SECRET_IN_CONFIG", conf_node.node_id)
                findings.append(RiskFinding(
                    finding_id=finding_id,
                    rule_id="RULE_PLAINTEXT_SECRET_IN_CONFIG",
                    title=f"Plaintext Sensitive Secret Assigned in {conf_node.metadata.get('declared_in', 'config')}: {conf_node.name}",
                    severity=Severity.HIGH,
                    risk_score=80.0,
                    explanation=(
                        f"Environment configuration variable '{conf_node.name}' appears to contain a hardcoded plaintext secret "
                        f"in '{conf_node.metadata.get('declared_in')}'. Committing secrets risks credential theft."
                    ),
                    evidence=[e.evidence for e in conf_edges],
                    affected_nodes=[conf_node.node_id],
                    remediation="Move secret values to environment secret managers and use .env.example with placeholder values.",
                ))

        # Rule 5: Circular Dependency Cycles
        cycles = traversal.detect_dependency_cycles()
        if cycles:
            for cycle in cycles[:5]:
                cycle_str = " -> ".join([graph.get_node(nid).name if graph.get_node(nid) else nid for nid in cycle])
                finding_id = deterministic_finding_id("RULE_CIRCULAR_DEPENDENCY_CYCLE", cycle_str)
                findings.append(RiskFinding(
                    finding_id=finding_id,
                    rule_id="RULE_CIRCULAR_DEPENDENCY_CYCLE",
                    title=f"Circular Dependency Cycle Detected ({len(cycle)-1} nodes)",
                    severity=Severity.MEDIUM,
                    risk_score=45.0,
                    explanation=(
                        f"Discovered circular import loop: {cycle_str}. "
                        "Circular dependencies impede static analysis, create tight coupling, and cause runtime initialization deadlocks."
                    ),
                    evidence=[EdgeEvidence(source_file=cycle[0], snippet=cycle_str)],
                    affected_nodes=cycle,
                    remediation="Refactor shared types or functions into an independent common module.",
                ))

        # Rule 6: High Centrality Single-Point-of-Failure Dependencies
        for dep_node in graph.list_nodes(NodeType.DEPENDENCY):
            in_degree = len(graph.get_in_edges(dep_node.node_id))
            if in_degree >= 4:
                blast = blast_estimator.estimate_blast_radius(dep_node.node_id)
                finding_id = deterministic_finding_id("RULE_HIGH_CENTRALITY_DEPENDENCY_BOTTLENECK", dep_node.node_id)
                findings.append(RiskFinding(
                    finding_id=finding_id,
                    rule_id="RULE_HIGH_CENTRALITY_DEPENDENCY_BOTTLENECK",
                    title=f"High-Centrality Core Dependency: {dep_node.name} ({in_degree} direct dependents)",
                    severity=Severity.LOW,
                    risk_score=25.0,
                    explanation=(
                        f"Package '{dep_node.name}' is a high-centrality dependency used across {in_degree} distinct files. "
                        f"A compromise or breaking change in this dependency impacts {blast['impacted_node_count']} nodes in the repository."
                    ),
                    evidence=[e.evidence for e in graph.get_in_edges(dep_node.node_id)[:3]],
                    affected_nodes=[dep_node.node_id],
                    remediation="Ensure this core package is pinned, actively monitored, and covered by automated regression tests.",
                ))

        # Sort findings deterministically by risk score descending, then finding_id
        findings.sort(key=lambda f: (-f.risk_score, f.finding_id))
        return findings
