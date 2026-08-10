"""
Environment Variable & .env File Parser.
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

SECRET_PATTERNS = re.compile(
    r"(api_key|secret|token|password|auth|private_key|aws_access_key|jwt)",
    re.IGNORECASE,
)


class EnvConfigParser(BaseParser):
    """Extracts environment variables, service references, and secret indicators from .env files."""

    def can_parse(self, file_path: Path, relative_path: str) -> bool:
        name = file_path.name.lower()
        return name == ".env" or name.startswith(".env.") or name == "env.example"

    def parse(
        self,
        file_path: Path,
        relative_path: str,
        content: str,
    ) -> List[Tuple[GraphNode, GraphEdge]]:
        results: List[Tuple[GraphNode, GraphEdge]] = []
        file_node_id = f"file:{relative_path}"

        for line_no, raw_line in enumerate(content.splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                var_name, _, var_val = line.partition("=")
                var_name = var_name.strip()
                var_val = var_val.strip()

                is_secret_key = bool(SECRET_PATTERNS.search(var_name))
                is_plaintext_secret = is_secret_key and len(var_val) > 8 and not var_val.startswith(("<", "YOUR_", "CHANGE_ME", "example", "xxx", "TODO"))

                conf_node_id = f"config:env/{var_name}"
                conf_node = GraphNode(
                    node_id=conf_node_id,
                    node_type=NodeType.CONFIGURATION,
                    name=var_name,
                    metadata={
                        "is_secret_key": is_secret_key,
                        "is_plaintext_secret": is_plaintext_secret,
                        "has_default_value": bool(var_val),
                        "declared_in": relative_path,
                    },
                )

                edge = GraphEdge(
                    source_id=file_node_id,
                    target_id=conf_node_id,
                    edge_type=EdgeType.CONFIGURES,
                    evidence=EdgeEvidence(
                        source_file=relative_path,
                        line_number=line_no,
                        extraction_method="env_var_parser",
                        confidence_score=1.0,
                        snippet=f"{var_name}=...",
                    ),
                    metadata={"is_secret_key": is_secret_key, "is_plaintext_secret": is_plaintext_secret},
                )
                results.append((conf_node, edge))

        return results
