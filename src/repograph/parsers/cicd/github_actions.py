"""
GitHub Actions CI/CD Workflow Analyzer for Repograph.

Statically parses workflow YAML files to map automation pipelines, third-party action dependencies,
secret reference trust boundaries, and supply-chain attack vectors.
"""

from __future__ import annotations

import re
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

SECRET_PATTERN = re.compile(r"\$\{\{\s*secrets\.([a-zA-Z0-9_]+)\s*\}\}")
ENV_PATTERN = re.compile(r"\$\{\{\s*env\.([a-zA-Z0-9_]+)\s*\}\}")


class GitHubActionsParser(BaseParser):
    """Extracts execution steps, action dependencies, secret trust edges, and deployment indicators."""

    def can_parse(self, file_path: Path, relative_path: str) -> bool:
        normalized = relative_path.replace("\\", "/")
        return (
            ".github/workflows" in normalized
            and file_path.suffix.lower() in (".yml", ".yaml")
        )

    def parse(
        self,
        file_path: Path,
        relative_path: str,
        content: str,
    ) -> List[Tuple[GraphNode, GraphEdge]]:
        results: List[Tuple[GraphNode, GraphEdge]] = []
        file_node_id = f"file:{relative_path}"

        try:
            data = yaml.safe_load(content)
        except Exception:
            return results

        if not isinstance(data, dict):
            return results

        workflow_name = data.get("name", file_path.stem)
        triggers = data.get("on", data.get(True, []))  # yaml True can parse as bool if unquoted 'on:'
        if isinstance(triggers, str):
            triggers_list = [triggers]
        elif isinstance(triggers, list):
            triggers_list = triggers
        elif isinstance(triggers, dict):
            triggers_list = list(triggers.keys())
        else:
            triggers_list = []

        is_pull_request_target = "pull_request_target" in triggers_list

        wf_node_id = f"workflow:{relative_path}"
        wf_node = GraphNode(
            node_id=wf_node_id,
            node_type=NodeType.WORKFLOW,
            name=str(workflow_name),
            path=relative_path,
            metadata={
                "triggers": triggers_list,
                "is_pull_request_target": is_pull_request_target,
            },
        )

        wf_edge = GraphEdge(
            source_id=file_node_id,
            target_id=wf_node_id,
            edge_type=EdgeType.CONTAINS,
            evidence=EdgeEvidence(
                source_file=relative_path,
                extraction_method="github_actions_workflow_def",
                confidence_score=1.0,
                snippet=f"name: {workflow_name}",
            ),
        )
        results.append((wf_node, wf_edge))

        # Parse jobs
        jobs = data.get("jobs", {})
        if isinstance(jobs, dict):
            for job_id, job_spec in jobs.items():
                if not isinstance(job_spec, dict):
                    continue

                steps = job_spec.get("steps", [])
                if not isinstance(steps, list):
                    continue

                for step in steps:
                    if not isinstance(step, dict):
                        continue

                    # 1. Check external actions 'uses: actions/checkout@v4'
                    if "uses" in step:
                        action_ref = str(step["uses"]).strip()
                        is_pinned_sha = bool(re.search(r"@[a-f0-9]{40}$", action_ref))
                        is_third_party = not action_ref.startswith(("actions/", "github/"))

                        action_node_id = f"pkg:github-action/{action_ref}"
                        action_node = GraphNode(
                            node_id=action_node_id,
                            node_type=NodeType.DEPENDENCY,
                            name=action_ref,
                            metadata={
                                "ecosystem": "github-actions",
                                "is_pinned_sha": is_pinned_sha,
                                "is_third_party": is_third_party,
                            },
                        )

                        action_edge = GraphEdge(
                            source_id=wf_node_id,
                            target_id=action_node_id,
                            edge_type=EdgeType.EXECUTES,
                            evidence=EdgeEvidence(
                                source_file=relative_path,
                                extraction_method="github_actions_step_uses",
                                confidence_score=1.0,
                                snippet=f"uses: {action_ref}",
                            ),
                            metadata={"is_pinned_sha": is_pinned_sha, "is_third_party": is_third_party},
                        )
                        results.append((action_node, action_edge))

                        # Trust edge for 3rd party actions
                        if is_third_party:
                            trust_edge = GraphEdge(
                                source_id=wf_node_id,
                                target_id=action_node_id,
                                edge_type=EdgeType.TRUSTS,
                                evidence=EdgeEvidence(
                                    source_file=relative_path,
                                    extraction_method="github_actions_third_party_action",
                                    confidence_score=1.0,
                                    snippet=f"uses: {action_ref}",
                                ),
                            )
                            results.append((action_node, trust_edge))

                    # 2. Check secret usage references
                    step_str = str(step)
                    for sec_match in SECRET_PATTERN.finditer(step_str):
                        secret_name = sec_match.group(1)
                        sec_node_id = f"config:secret/{secret_name}"
                        sec_node = GraphNode(
                            node_id=sec_node_id,
                            node_type=NodeType.CONFIGURATION,
                            name=f"Secret: {secret_name}",
                            metadata={"is_github_secret": True},
                        )
                        sec_edge = GraphEdge(
                            source_id=wf_node_id,
                            target_id=sec_node_id,
                            edge_type=EdgeType.TRUSTS,
                            evidence=EdgeEvidence(
                                source_file=relative_path,
                                extraction_method="github_actions_secret_ref",
                                confidence_score=1.0,
                                snippet=f"${{{{ secrets.{secret_name} }}}}",
                            ),
                            metadata={"is_pull_request_target": is_pull_request_target},
                        )
                        results.append((sec_node, sec_edge))

        return results
