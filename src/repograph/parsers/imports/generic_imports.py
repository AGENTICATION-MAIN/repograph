"""
Go and Rust Source Code Import Extractors.
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


class GoImportParser(BaseParser):
    """Extracts imported packages from Go (.go) source files."""

    def can_parse(self, file_path: Path, relative_path: str) -> bool:
        return file_path.suffix.lower() == ".go"

    def parse(
        self,
        file_path: Path,
        relative_path: str,
        content: str,
    ) -> List[Tuple[GraphNode, GraphEdge]]:
        results = []
        file_node_id = f"file:{relative_path}"
        lines = content.splitlines()

        in_import_block = False
        for line_no, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if line.startswith("import ("):
                in_import_block = True
                continue
            elif in_import_block and line.startswith(")"):
                in_import_block = False
                continue

            if in_import_block or line.startswith("import "):
                match = re.search(r'["\']([^"\']+)["\']', line)
                if match:
                    pkg = match.group(1).strip()
                    target_id = f"module:{pkg}"
                    mod_node = GraphNode(node_id=target_id, node_type=NodeType.MODULE, name=pkg)
                    edge = GraphEdge(
                        source_id=file_node_id,
                        target_id=target_id,
                        edge_type=EdgeType.IMPORTS,
                        evidence=EdgeEvidence(
                            source_file=relative_path,
                            line_number=line_no,
                            extraction_method="go_source_import",
                            confidence_score=1.0,
                            snippet=line,
                        ),
                    )
                    results.append((mod_node, edge))

        return results


class RustImportParser(BaseParser):
    """Extracts crates and modules from Rust (.rs) source files."""

    def can_parse(self, file_path: Path, relative_path: str) -> bool:
        return file_path.suffix.lower() == ".rs"

    def parse(
        self,
        file_path: Path,
        relative_path: str,
        content: str,
    ) -> List[Tuple[GraphNode, GraphEdge]]:
        results = []
        file_node_id = f"file:{relative_path}"
        lines = content.splitlines()

        for line_no, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            # Match "use foo::bar;" or "extern crate foo;"
            m_use = re.match(r"^(?:pub\s+)?use\s+([a-zA-Z0-9_]+)", line)
            if m_use:
                crate = m_use.group(1)
                if crate not in ("crate", "super", "self"):
                    target_id = f"module:{crate}"
                    mod_node = GraphNode(node_id=target_id, node_type=NodeType.MODULE, name=crate)
                    edge = GraphEdge(
                        source_id=file_node_id,
                        target_id=target_id,
                        edge_type=EdgeType.IMPORTS,
                        evidence=EdgeEvidence(
                            source_file=relative_path,
                            line_number=line_no,
                            extraction_method="rust_use_import",
                            confidence_score=0.95,
                            snippet=line,
                        ),
                    )
                    results.append((mod_node, edge))

        return results
