"""
Rust Cargo Dependency Parser (Cargo.toml).
"""

from __future__ import annotations

import tomllib
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


class RustDependencyParser(BaseParser):
    """Extracts Rust crate dependencies from Cargo.toml."""

    def can_parse(self, file_path: Path, relative_path: str) -> bool:
        return file_path.name.lower() == "cargo.toml"

    def parse(
        self,
        file_path: Path,
        relative_path: str,
        content: str,
    ) -> List[Tuple[GraphNode, GraphEdge]]:
        results: List[Tuple[GraphNode, GraphEdge]] = []
        file_node_id = f"file:{relative_path}"

        try:
            data = tomllib.loads(content)
        except Exception:
            return results

        sections = [
            ("dependencies", "runtime"),
            ("dev-dependencies", "dev"),
            ("build-dependencies", "build"),
        ]

        for sec_name, scope in sections:
            deps = data.get(sec_name, {})
            if isinstance(deps, dict):
                for crate_name, spec in deps.items():
                    if isinstance(spec, str):
                        version = spec
                    elif isinstance(spec, dict):
                        version = str(spec.get("version", "*"))
                    else:
                        version = "*"

                    dep_node_id = f"pkg:cargo/{crate_name}"
                    dep_node = GraphNode(
                        node_id=dep_node_id,
                        node_type=NodeType.DEPENDENCY,
                        name=crate_name,
                        metadata={
                            "ecosystem": "cargo",
                            "version_constraint": version,
                            "scope": scope,
                            "declared_in": relative_path,
                        },
                    )

                    edge = GraphEdge(
                        source_id=file_node_id,
                        target_id=dep_node_id,
                        edge_type=EdgeType.DEPENDS_ON,
                        evidence=EdgeEvidence(
                            source_file=relative_path,
                            extraction_method=f"cargo_toml_{sec_name}",
                            confidence_score=1.0,
                            snippet=f"{crate_name} = {version}",
                        ),
                        metadata={"scope": scope, "version_constraint": version},
                    )
                    results.append((dep_node, edge))

        return results
