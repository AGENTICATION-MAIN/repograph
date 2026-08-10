"""
Node.js / npm Dependency Manifest Parser (package.json).
"""

from __future__ import annotations

import json
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


class NodeDependencyParser(BaseParser):
    """Extracts npm/JavaScript package dependencies from package.json."""

    def can_parse(self, file_path: Path, relative_path: str) -> bool:
        return file_path.name.lower() == "package.json"

    def parse(
        self,
        file_path: Path,
        relative_path: str,
        content: str,
    ) -> List[Tuple[GraphNode, GraphEdge]]:
        results: List[Tuple[GraphNode, GraphEdge]] = []
        file_node_id = f"file:{relative_path}"

        try:
            data = json.loads(content)
        except Exception:
            return results

        scopes = [
            ("dependencies", "runtime"),
            ("devDependencies", "dev"),
            ("peerDependencies", "peer"),
            ("optionalDependencies", "optional"),
        ]

        for section_key, scope_name in scopes:
            section = data.get(section_key, {})
            if isinstance(section, dict):
                for pkg_name, version_spec in section.items():
                    constraint = str(version_spec)
                    dep_node_id = f"pkg:npm/{pkg_name}"
                    dep_node = GraphNode(
                        node_id=dep_node_id,
                        node_type=NodeType.DEPENDENCY,
                        name=pkg_name,
                        metadata={
                            "ecosystem": "npm",
                            "version_constraint": constraint,
                            "scope": scope_name,
                            "declared_in": relative_path,
                        },
                    )

                    edge = GraphEdge(
                        source_id=file_node_id,
                        target_id=dep_node_id,
                        edge_type=EdgeType.DEPENDS_ON,
                        evidence=EdgeEvidence(
                            source_file=relative_path,
                            extraction_method=f"package_json_{section_key}",
                            confidence_score=1.0,
                            snippet=f'"{pkg_name}": "{constraint}"',
                        ),
                        metadata={"scope": scope_name, "version_constraint": constraint},
                    )
                    results.append((dep_node, edge))

        return results
