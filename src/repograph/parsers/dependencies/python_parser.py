"""
Python Dependency Manifest Parser (requirements.txt, pyproject.toml, setup.py).
"""

from __future__ import annotations

import re
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


class PythonDependencyParser(BaseParser):
    """Extracts Python package dependencies and version constraints from manifests."""

    def can_parse(self, file_path: Path, relative_path: str) -> bool:
        name = file_path.name.lower()
        return (
            name == "requirements.txt"
            or name.startswith("requirements") and name.endswith(".txt")
            or name.endswith("-requirements.txt")
            or name == "pyproject.toml"
            or name == "setup.py"
        )

    def parse(
        self,
        file_path: Path,
        relative_path: str,
        content: str,
    ) -> List[Tuple[GraphNode, GraphEdge]]:
        """Extracts dependency nodes and DEPENDS_ON edges."""
        results: List[Tuple[GraphNode, GraphEdge]] = []
        name = file_path.name.lower()

        if name.endswith(".txt"):
            results.extend(self._parse_requirements_txt(relative_path, content))
        elif name == "pyproject.toml":
            results.extend(self._parse_pyproject_toml(relative_path, content))
        elif name == "setup.py":
            results.extend(self._parse_setup_py(relative_path, content))

        return results

    def _parse_requirements_txt(self, relative_path: str, content: str) -> List[Tuple[GraphNode, GraphEdge]]:
        results = []
        file_node_id = f"file:{relative_path}"

        for line_no, raw_line in enumerate(content.splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("-r") or line.startswith("--"):
                continue

            # Remove inline comments and environment markers
            line_no_comment = line.split("#")[0].strip()
            line_clean = line_no_comment.split(";")[0].strip()

            # Extract package name and version: e.g. "fastapi>=0.110.0", "requests==2.31.0", "pydantic"
            match = re.match(r"^([a-zA-Z0-9_\-\.]+)(.*)$", line_clean)
            if match:
                pkg_name = match.group(1).lower().replace("_", "-")
                version_constraint = match.group(2).strip() or "*"

                dep_node_id = f"pkg:pypi/{pkg_name}"
                dep_node = GraphNode(
                    node_id=dep_node_id,
                    node_type=NodeType.DEPENDENCY,
                    name=pkg_name,
                    metadata={
                        "ecosystem": "pypi",
                        "version_constraint": version_constraint,
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
                        extraction_method="python_requirements_txt",
                        confidence_score=1.0,
                        snippet=raw_line.strip(),
                    ),
                    metadata={"version_constraint": version_constraint},
                )
                results.append((dep_node, edge))

        return results

    def _parse_pyproject_toml(self, relative_path: str, content: str) -> List[Tuple[GraphNode, GraphEdge]]:
        results = []
        file_node_id = f"file:{relative_path}"

        try:
            data = tomllib.loads(content)
        except Exception:
            return results

        # 1. Standard PEP 621 [project.dependencies]
        dependencies = data.get("project", {}).get("dependencies", [])
        if isinstance(dependencies, list):
            for dep_str in dependencies:
                match = re.match(r"^([a-zA-Z0-9_\-\.]+)(.*)$", dep_str.strip())
                if match:
                    pkg_name = match.group(1).lower().replace("_", "-")
                    constraint = match.group(2).strip() or "*"
                    dep_node_id = f"pkg:pypi/{pkg_name}"
                    dep_node = GraphNode(
                        node_id=dep_node_id,
                        node_type=NodeType.DEPENDENCY,
                        name=pkg_name,
                        metadata={"ecosystem": "pypi", "version_constraint": constraint, "scope": "runtime"},
                    )
                    edge = GraphEdge(
                        source_id=file_node_id,
                        target_id=dep_node_id,
                        edge_type=EdgeType.DEPENDS_ON,
                        evidence=EdgeEvidence(
                            source_file=relative_path,
                            extraction_method="pep621_pyproject_toml",
                            confidence_score=1.0,
                            snippet=dep_str,
                        ),
                        metadata={"version_constraint": constraint},
                    )
                    results.append((dep_node, edge))

        # 2. Poetry [tool.poetry.dependencies]
        poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
        if isinstance(poetry_deps, dict):
            for pkg, spec in poetry_deps.items():
                if pkg.lower() == "python":
                    continue
                pkg_name = pkg.lower().replace("_", "-")
                constraint = spec if isinstance(spec, str) else str(spec.get("version", "*"))
                dep_node_id = f"pkg:pypi/{pkg_name}"
                dep_node = GraphNode(
                    node_id=dep_node_id,
                    node_type=NodeType.DEPENDENCY,
                    name=pkg_name,
                    metadata={"ecosystem": "pypi", "version_constraint": constraint, "scope": "runtime"},
                )
                edge = GraphEdge(
                    source_id=file_node_id,
                    target_id=dep_node_id,
                    edge_type=EdgeType.DEPENDS_ON,
                    evidence=EdgeEvidence(
                        source_file=relative_path,
                        extraction_method="poetry_pyproject_toml",
                        confidence_score=1.0,
                        snippet=f"{pkg} = {constraint}",
                    ),
                    metadata={"version_constraint": constraint},
                )
                results.append((dep_node, edge))

        return results

    def _parse_setup_py(self, relative_path: str, content: str) -> List[Tuple[GraphNode, GraphEdge]]:
        results = []
        file_node_id = f"file:{relative_path}"

        # Match install_requires=[...]
        match = re.search(r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL)
        if match:
            block = match.group(1)
            raw_deps = re.findall(r"['\"]([a-zA-Z0-9_\-\.><=~!^]+)['\"]", block)
            for dep_str in raw_deps:
                m = re.match(r"^([a-zA-Z0-9_\-\.]+)(.*)$", dep_str.strip())
                if m:
                    pkg_name = m.group(1).lower().replace("_", "-")
                    constraint = m.group(2).strip() or "*"
                    dep_node_id = f"pkg:pypi/{pkg_name}"
                    dep_node = GraphNode(
                        node_id=dep_node_id,
                        node_type=NodeType.DEPENDENCY,
                        name=pkg_name,
                        metadata={"ecosystem": "pypi", "version_constraint": constraint},
                    )
                    edge = GraphEdge(
                        source_id=file_node_id,
                        target_id=dep_node_id,
                        edge_type=EdgeType.DEPENDS_ON,
                        evidence=EdgeEvidence(
                            source_file=relative_path,
                            extraction_method="setup_py_install_requires",
                            confidence_score=0.95,
                            snippet=dep_str,
                        ),
                        metadata={"version_constraint": constraint},
                    )
                    results.append((dep_node, edge))

        return results
