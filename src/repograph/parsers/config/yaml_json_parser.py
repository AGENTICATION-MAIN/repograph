"""
General YAML and JSON Configuration File Parser.
"""

from __future__ import annotations

import json
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


class GenericConfigParser(BaseParser):
    """Parses arbitrary YAML and JSON config files (e.g. tsconfig.json, serverless.yml, k8s)."""

    def can_parse(self, file_path: Path, relative_path: str) -> bool:
        if ".github/workflows" in relative_path.replace("\\", "/"):
            return False  # Handled by CI/CD parser
        name = file_path.name.lower()
        if name in ("package.json", "docker-compose.yml", "docker-compose.yaml"):
            return False  # Handled by specific parsers
        return file_path.suffix.lower() in (".json", ".yaml", ".yml")

    def parse(
        self,
        file_path: Path,
        relative_path: str,
        content: str,
    ) -> List[Tuple[GraphNode, GraphEdge]]:
        results = []
        file_node_id = f"file:{relative_path}"

        conf_node_id = f"config:{relative_path}"
        conf_node = GraphNode(
            node_id=conf_node_id,
            node_type=NodeType.CONFIGURATION,
            name=file_path.name,
            path=relative_path,
        )

        edge = GraphEdge(
            source_id=file_node_id,
            target_id=conf_node_id,
            edge_type=EdgeType.CONFIGURES,
            evidence=EdgeEvidence(
                source_file=relative_path,
                extraction_method="generic_config_parser",
                confidence_score=1.0,
                snippet=file_path.name,
            ),
        )
        results.append((conf_node, edge))
        return results
