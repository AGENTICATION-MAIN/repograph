"""
Dockerfile and Docker Compose Parser for Repograph.
"""

from __future__ import annotations

import re
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from repograph.core.types import (
    EdgeEvidence,
    EdgeType,
    GraphEdge,
    GraphNode,
    NodeType,
)
from repograph.parsers.base import BaseParser


class DockerConfigParser(BaseParser):
    """Extracts base images, exposed ports, and service topologies from Docker files."""

    def can_parse(self, file_path: Path, relative_path: str) -> bool:
        name = file_path.name.lower()
        return (
            name == "dockerfile"
            or name.startswith("dockerfile.")
            or name.endswith(".dockerfile")
            or "docker-compose" in name
        )

    def parse(
        self,
        file_path: Path,
        relative_path: str,
        content: str,
    ) -> List[Tuple[GraphNode, GraphEdge]]:
        results: List[Tuple[GraphNode, GraphEdge]] = []
        name = file_path.name.lower()

        if "docker-compose" in name:
            results.extend(self._parse_compose(relative_path, content))
        else:
            results.extend(self._parse_dockerfile(relative_path, content))

        return results

    def _parse_dockerfile(self, relative_path: str, content: str) -> List[Tuple[GraphNode, GraphEdge]]:
        results = []
        file_node_id = f"file:{relative_path}"

        for line_no, raw_line in enumerate(content.splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            # Parse FROM image:tag
            m_from = re.match(r"^FROM\s+([^\s]+)", line, re.IGNORECASE)
            if m_from:
                image_ref = m_from.group(1).strip()
                is_unpinned = (":" not in image_ref) or image_ref.endswith(":latest")
                target_id = f"pkg:docker/{image_ref}"
                dep_node = GraphNode(
                    node_id=target_id,
                    node_type=NodeType.DEPENDENCY,
                    name=image_ref,
                    metadata={"ecosystem": "docker", "is_unpinned_base": is_unpinned},
                )
                edge = GraphEdge(
                    source_id=file_node_id,
                    target_id=target_id,
                    edge_type=EdgeType.DEPENDS_ON,
                    evidence=EdgeEvidence(
                        source_file=relative_path,
                        line_number=line_no,
                        extraction_method="dockerfile_from",
                        confidence_score=1.0,
                        snippet=line,
                    ),
                    metadata={"is_unpinned_base": is_unpinned},
                )
                results.append((dep_node, edge))

            # Parse EXPOSE port
            m_exp = re.match(r"^EXPOSE\s+(\d+)", line, re.IGNORECASE)
            if m_exp:
                port = m_exp.group(1)
                target_id = f"service:port/{port}"
                svc_node = GraphNode(
                    node_id=target_id,
                    node_type=NodeType.SERVICE,
                    name=f"Port {port}",
                    metadata={"port": int(port)},
                )
                edge = GraphEdge(
                    source_id=file_node_id,
                    target_id=target_id,
                    edge_type=EdgeType.EXPOSES,
                    evidence=EdgeEvidence(
                        source_file=relative_path,
                        line_number=line_no,
                        extraction_method="dockerfile_expose",
                        confidence_score=1.0,
                        snippet=line,
                    ),
                )
                results.append((svc_node, edge))

        return results

    def _parse_compose(self, relative_path: str, content: str) -> List[Tuple[GraphNode, GraphEdge]]:
        results = []
        file_node_id = f"file:{relative_path}"

        try:
            data = yaml.safe_load(content)
        except Exception:
            return results

        if not isinstance(data, dict):
            return results

        services = data.get("services", {})
        if isinstance(services, dict):
            for svc_name, spec in services.items():
                svc_node_id = f"service:{svc_name}"
                svc_node = GraphNode(
                    node_id=svc_node_id,
                    node_type=NodeType.SERVICE,
                    name=svc_name,
                    metadata={"declared_in": relative_path},
                )
                edge = GraphEdge(
                    source_id=file_node_id,
                    target_id=svc_node_id,
                    edge_type=EdgeType.CONFIGURES,
                    evidence=EdgeEvidence(
                        source_file=relative_path,
                        extraction_method="docker_compose_service",
                        confidence_score=1.0,
                        snippet=f"service: {svc_name}",
                    ),
                )
                results.append((svc_node, edge))

                # Check depends_on relationships between services
                if isinstance(spec, dict):
                    depends_on = spec.get("depends_on", [])
                    if isinstance(depends_on, list):
                        for dep_svc in depends_on:
                            dep_svc_id = f"service:{dep_svc}"
                            dep_edge = GraphEdge(
                                source_id=svc_node_id,
                                target_id=dep_svc_id,
                                edge_type=EdgeType.DEPENDS_ON,
                                evidence=EdgeEvidence(
                                    source_file=relative_path,
                                    extraction_method="compose_depends_on",
                                    confidence_score=1.0,
                                    snippet=f"{svc_name} -> {dep_svc}",
                                ),
                            )
                            results.append((GraphNode(node_id=dep_svc_id, node_type=NodeType.SERVICE, name=dep_svc), dep_edge))

        return results
