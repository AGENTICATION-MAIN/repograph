"""
Python AST Source Code Import Extractor.
"""

from __future__ import annotations

import ast
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


class PythonImportParser(BaseParser):
    """Extracts internal and external import dependencies from Python source files using AST."""

    def can_parse(self, file_path: Path, relative_path: str) -> bool:
        return file_path.suffix.lower() == ".py" and file_path.name != "setup.py"

    def parse(
        self,
        file_path: Path,
        relative_path: str,
        content: str,
    ) -> List[Tuple[GraphNode, GraphEdge]]:
        results: List[Tuple[GraphNode, GraphEdge]] = []
        file_node_id = f"file:{relative_path}"

        try:
            tree = ast.parse(content, filename=relative_path)
        except SyntaxError:
            # Fallback to regex if file has Python syntax error
            return self._regex_fallback(relative_path, content)
        except Exception:
            return results

        lines = content.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    line_no = getattr(node, "lineno", None)
                    snippet = lines[line_no - 1].strip() if line_no and line_no <= len(lines) else f"import {module_name}"

                    target_node_id = f"module:{module_name}"
                    mod_node = GraphNode(
                        node_id=target_node_id,
                        node_type=NodeType.MODULE,
                        name=module_name,
                    )
                    edge = GraphEdge(
                        source_id=file_node_id,
                        target_id=target_node_id,
                        edge_type=EdgeType.IMPORTS,
                        evidence=EdgeEvidence(
                            source_file=relative_path,
                            line_number=line_no,
                            extraction_method="python_ast_import",
                            confidence_score=1.0,
                            snippet=snippet,
                        ),
                    )
                    results.append((mod_node, edge))

            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                # Handle relative imports (e.g. from . import utils -> level=1)
                prefix = "." * (node.level or 0)
                full_mod = f"{prefix}{module_name}" if prefix else module_name
                line_no = getattr(node, "lineno", None)
                snippet = lines[line_no - 1].strip() if line_no and line_no <= len(lines) else f"from {full_mod} import ..."

                target_node_id = f"module:{full_mod}"
                mod_node = GraphNode(
                    node_id=target_node_id,
                    node_type=NodeType.MODULE,
                    name=full_mod,
                )
                edge = GraphEdge(
                    source_id=file_node_id,
                    target_id=target_node_id,
                    edge_type=EdgeType.IMPORTS,
                    evidence=EdgeEvidence(
                        source_file=relative_path,
                        line_number=line_no,
                        extraction_method="python_ast_from_import",
                        confidence_score=1.0,
                        snippet=snippet,
                    ),
                )
                results.append((mod_node, edge))

        return results

    def _regex_fallback(self, relative_path: str, content: str) -> List[Tuple[GraphNode, GraphEdge]]:
        import re
        results = []
        file_node_id = f"file:{relative_path}"
        lines = content.splitlines()

        for line_no, line in enumerate(lines, start=1):
            line_str = line.strip()
            # match "import foo"
            m_imp = re.match(r"^import\s+([a-zA-Z0-9_\.]+)", line_str)
            if m_imp:
                mod = m_imp.group(1)
                target_node_id = f"module:{mod}"
                mod_node = GraphNode(node_id=target_node_id, node_type=NodeType.MODULE, name=mod)
                edge = GraphEdge(
                    source_id=file_node_id,
                    target_id=target_node_id,
                    edge_type=EdgeType.IMPORTS,
                    evidence=EdgeEvidence(
                        source_file=relative_path,
                        line_number=line_no,
                        extraction_method="python_regex_fallback",
                        confidence_score=0.85,
                        snippet=line_str,
                    ),
                )
                results.append((mod_node, edge))

            # match "from foo import bar"
            m_from = re.match(r"^from\s+([a-zA-Z0-9_\.]+)\s+import", line_str)
            if m_from:
                mod = m_from.group(1)
                target_node_id = f"module:{mod}"
                mod_node = GraphNode(node_id=target_node_id, node_type=NodeType.MODULE, name=mod)
                edge = GraphEdge(
                    source_id=file_node_id,
                    target_id=target_node_id,
                    edge_type=EdgeType.IMPORTS,
                    evidence=EdgeEvidence(
                        source_file=relative_path,
                        line_number=line_no,
                        extraction_method="python_regex_fallback",
                        confidence_score=0.85,
                        snippet=line_str,
                    ),
                )
                results.append((mod_node, edge))

        return results
