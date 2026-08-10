"""
JavaScript & TypeScript Import Extractor.
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

JS_TS_EXTENSIONS = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}


class JavaScriptImportParser(BaseParser):
    """Extracts ESM and CommonJS imports from JavaScript/TypeScript source files."""

    def can_parse(self, file_path: Path, relative_path: str) -> bool:
        return file_path.suffix.lower() in JS_TS_EXTENSIONS and file_path.name != "package.json"

    def parse(
        self,
        file_path: Path,
        relative_path: str,
        content: str,
    ) -> List[Tuple[GraphNode, GraphEdge]]:
        results: List[Tuple[GraphNode, GraphEdge]] = []
        file_node_id = f"file:{relative_path}"
        lines = content.splitlines()

        # Regular expressions for JS/TS import syntax
        # 1. import ... from 'module'
        # 2. import 'module'
        # 3. require('module')
        # 4. export * from 'module'
        esm_from_regex = re.compile(r"""(?:import|export)\s+(?:.*?from\s+)?['"]([^'"]+)['"]""")
        require_regex = re.compile(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""")

        for line_no, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line or line.startswith("//") or line.startswith("/*") or line.startswith("*"):
                continue

            # Match ESM imports
            for match in esm_from_regex.finditer(line):
                import_path = match.group(1).strip()
                if import_path:
                    is_relative = import_path.startswith(".") or import_path.startswith("/")
                    target_node_id = f"file:{import_path}" if is_relative else f"pkg:npm/{import_path}"
                    mod_node = GraphNode(
                        node_id=target_node_id,
                        node_type=NodeType.FILE if is_relative else NodeType.DEPENDENCY,
                        name=import_path,
                        metadata={"is_relative": is_relative},
                    )
                    edge = GraphEdge(
                        source_id=file_node_id,
                        target_id=target_node_id,
                        edge_type=EdgeType.IMPORTS,
                        evidence=EdgeEvidence(
                            source_file=relative_path,
                            line_number=line_no,
                            extraction_method="js_esm_import",
                            confidence_score=1.0,
                            snippet=line,
                        ),
                    )
                    results.append((mod_node, edge))

            # Match CommonJS require
            for match in require_regex.finditer(line):
                import_path = match.group(1).strip()
                if import_path:
                    is_relative = import_path.startswith(".") or import_path.startswith("/")
                    target_node_id = f"file:{import_path}" if is_relative else f"pkg:npm/{import_path}"
                    mod_node = GraphNode(
                        node_id=target_node_id,
                        node_type=NodeType.FILE if is_relative else NodeType.DEPENDENCY,
                        name=import_path,
                        metadata={"is_relative": is_relative},
                    )
                    edge = GraphEdge(
                        source_id=file_node_id,
                        target_id=target_node_id,
                        edge_type=EdgeType.IMPORTS,
                        evidence=EdgeEvidence(
                            source_file=relative_path,
                            line_number=line_no,
                            extraction_method="js_commonjs_require",
                            confidence_score=1.0,
                            snippet=line,
                        ),
                    )
                    results.append((mod_node, edge))

        return results
