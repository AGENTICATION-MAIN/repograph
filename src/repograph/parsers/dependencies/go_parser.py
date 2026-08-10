"""
Go Module Dependency Parser (go.mod).
"""

from __future__ import annotations

import re
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


class GoDependencyParser(BaseParser):
    """Extracts Go module dependencies from go.mod."""

    def can_parse(self, file_path: Path, relative_path: str) -> bool:
        return file_path.name.lower() == "go.mod"

    def parse(
        self,
        file_path: Path,
        relative_path: str,
        content: str,
    ) -> List[Tuple[GraphNode, GraphEdge]]:
        results: List[Tuple[GraphNode, GraphEdge]] = []
        file_node_id = f"file:{relative_path}"

        lines = content.splitlines()
        in_require_block = False

        for line_no, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line or line.startswith("//"):
                continue

            if line.startswith("require ("):
                in_require_block = True
                continue
            elif in_require_block and line.startswith(")"):
                in_require_block = False
                continue

            if in_require_block or line.startswith("require "):
                line_content = line.removeprefix("require ").strip()
                is_indirect = "// indirect" in line_content
                cleaned = line_content.split("//")[0].strip()

                parts = cleaned.split()
                if len(parts) >= 2:
                    mod_path = parts[0]
                    version = parts[1]

                    dep_node_id = f"pkg:golang/{mod_path}"
                    dep_node = GraphNode(
                        node_id=dep_node_id,
                        node_type=NodeType.DEPENDENCY,
                        name=mod_path,
                        metadata={
                            "ecosystem": "golang",
                            "version_constraint": version,
                            "is_indirect": is_indirect,
                            "declared_in": relative_path,
                        },
                    )

                    edge = GraphEdge(
                        source_id=file_node_id,
                        target_id=dep_node_id,
                        edge_type=EdgeType.DEPENDS_ON,
                        evidence=EdgeEvidence(
                            source_file=relative_path,
                            line_number=line_no,
                            extraction_method="go_mod_parser",
                            confidence_score=1.0,
                            snippet=raw_line.strip(),
                        ),
                        metadata={"version_constraint": version, "is_indirect": is_indirect},
                    )
                    results.append((dep_node, edge))

        return results
