"""
Repository Intelligence Graph Builder for Repograph.

Coordinates file tree scanning, multi-ecosystem dependency parsing,
source import extraction, module-to-file resolution, configuration analysis,
and CI/CD workflow linking.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from repograph.core.config import RepographConfig
from repograph.core.types import (
    EdgeEvidence,
    EdgeType,
    GraphEdge,
    GraphNode,
    NodeType,
    ScanSummary,
)
from repograph.graph.model import RepositoryGraph
from repograph.parsers.base import BaseParser
from repograph.parsers.cicd.github_actions import GitHubActionsParser
from repograph.parsers.config.docker_parser import DockerConfigParser
from repograph.parsers.config.env_parser import EnvConfigParser
from repograph.parsers.config.yaml_json_parser import GenericConfigParser
from repograph.parsers.dependencies.go_parser import GoDependencyParser
from repograph.parsers.dependencies.node_parser import NodeDependencyParser
from repograph.parsers.dependencies.python_parser import PythonDependencyParser
from repograph.parsers.dependencies.rust_parser import RustDependencyParser
from repograph.parsers.imports.generic_imports import GoImportParser, RustImportParser
from repograph.parsers.imports.js_ts_imports import JavaScriptImportParser
from repograph.parsers.imports.python_imports import PythonImportParser
from repograph.scanner.file_walker import FileWalker


class GraphBuilder:
    """
    Constructs a unified, fully cross-linked Repository Intelligence Graph from source files.
    """

    def __init__(self, root_path: Path, config: Optional[RepographConfig] = None):
        self.root_path = root_path.resolve()
        self.config = config or RepographConfig()
        self.walker = FileWalker(self.root_path, self.config)

        # Standard parser registry
        self.parsers: List[BaseParser] = [
            # Manifest Dependency Parsers
            PythonDependencyParser(),
            NodeDependencyParser(),
            GoDependencyParser(),
            RustDependencyParser(),
            # Source Import Parsers
            PythonImportParser(),
            JavaScriptImportParser(),
            GoImportParser(),
            RustImportParser(),
            # Configuration Parsers
            EnvConfigParser(),
            DockerConfigParser(),
            GenericConfigParser(),
            # CI/CD Parsers
            GitHubActionsParser(),
        ]

    def build_graph(self) -> Tuple[RepositoryGraph, ScanSummary]:
        """
        Executes end-to-end static scanning, graph synthesis, and internal module resolution.
        Returns the populated RepositoryGraph and ScanSummary.
        """
        start_time = time.perf_counter()

        graph = RepositoryGraph(root_name=self.root_path.name)
        summary = ScanSummary(repository_path=str(self.root_path))

        # Root Repository Node
        repo_node_id = f"repo:{self.root_path.name}"
        repo_node = GraphNode(
            node_id=repo_node_id,
            node_type=NodeType.REPOSITORY,
            name=self.root_path.name,
            path=".",
        )
        graph.add_node(repo_node)

        discovered_dirs: Set[str] = set()
        file_stem_map: Dict[str, str] = {}  # "app" -> "file:src/app.py", "src/app" -> "file:src/app.py"

        for abs_file, rel_file, meta in self.walker.walk():
            summary.total_files += 1
            lang = meta.get("language", "Unknown")
            summary.languages[lang] = summary.languages.get(lang, 0) + 1

            rel_path_obj = Path(rel_file)
            file_node_id = f"file:{rel_file}"

            # Index file paths for module resolution
            stem = rel_path_obj.stem
            file_stem_map[stem] = file_node_id
            file_stem_map[rel_file] = file_node_id
            posix_no_ext = rel_path_obj.with_suffix("").as_posix()
            file_stem_map[posix_no_ext] = file_node_id
            dotted = posix_no_ext.replace("/", ".")
            file_stem_map[dotted] = file_node_id

            # Register parent directory nodes
            if len(rel_path_obj.parts) > 1:
                parent_dir_rel = rel_path_obj.parent.as_posix()
                if parent_dir_rel not in discovered_dirs:
                    discovered_dirs.add(parent_dir_rel)
                    dir_node_id = f"dir:{parent_dir_rel}"
                    dir_node = GraphNode(
                        node_id=dir_node_id,
                        node_type=NodeType.DIRECTORY,
                        name=rel_path_obj.parent.name,
                        path=parent_dir_rel,
                    )
                    graph.add_node(dir_node)
                    # Edge: Repo -> Directory
                    graph.add_edge(GraphEdge(
                        source_id=repo_node_id,
                        target_id=dir_node_id,
                        edge_type=EdgeType.CONTAINS,
                        evidence=EdgeEvidence(source_file=parent_dir_rel, confidence_score=1.0),
                    ))

            # File Node
            file_node = GraphNode(
                node_id=file_node_id,
                node_type=NodeType.FILE,
                name=rel_path_obj.name,
                path=rel_file,
                metadata=meta,
            )
            graph.add_node(file_node)

            # Edge: Directory/Repo -> File
            parent_container_id = f"dir:{rel_path_obj.parent.as_posix()}" if len(rel_path_obj.parts) > 1 else repo_node_id
            graph.add_edge(GraphEdge(
                source_id=parent_container_id,
                target_id=file_node_id,
                edge_type=EdgeType.CONTAINS,
                evidence=EdgeEvidence(source_file=rel_file, confidence_score=1.0),
            ))

            # Read file content safely for parsing
            if meta.get("size_bytes", 0) <= self.config.max_file_size_bytes:
                try:
                    with open(abs_file, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Run applicable parsers
                    for parser in self.parsers:
                        if parser.can_parse(abs_file, rel_file):
                            extracted = parser.parse(abs_file, rel_file, content)
                            for target_node, edge in extracted:
                                graph.add_node(target_node)
                                graph.add_edge(edge)

                                # Update summary tracking
                                if target_node.node_type == NodeType.DEPENDENCY:
                                    summary.total_dependencies += 1
                                    eco = target_node.metadata.get("ecosystem")
                                    if eco:
                                        summary.ecosystems.add(eco)
                                elif target_node.node_type == NodeType.WORKFLOW:
                                    summary.total_workflows += 1
                                elif target_node.node_type == NodeType.CONFIGURATION:
                                    summary.total_configs += 1

                except Exception:
                    pass

        # Internal Module & Relative Import Cross-Linking Resolution
        for edge in list(graph.list_edges(EdgeType.IMPORTS)):
            target_node = graph.get_node(edge.target_id)
            if target_node and target_node.node_type == NodeType.MODULE:
                mod_name = target_node.name.lstrip(".")
                # Check relative path from source file directory
                source_node = graph.get_node(edge.source_id)
                if source_node and source_node.path:
                    source_dir = Path(source_node.path).parent
                    candidate_rel = (source_dir / mod_name).as_posix()
                    if candidate_rel in file_stem_map:
                        resolved_file_id = file_stem_map[candidate_rel]
                        graph.add_edge(GraphEdge(
                            source_id=edge.source_id,
                            target_id=resolved_file_id,
                            edge_type=EdgeType.IMPORTS,
                            evidence=edge.evidence,
                        ))
                    elif mod_name in file_stem_map:
                        resolved_file_id = file_stem_map[mod_name]
                        graph.add_edge(GraphEdge(
                            source_id=edge.source_id,
                            target_id=resolved_file_id,
                            edge_type=EdgeType.IMPORTS,
                            evidence=edge.evidence,
                        ))

        summary.total_directories = len(discovered_dirs)
        summary.total_nodes = graph.node_count
        summary.total_edges = graph.edge_count
        summary.scan_duration_seconds = time.perf_counter() - start_time

        return graph, summary
