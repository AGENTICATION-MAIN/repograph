"""
Unit tests for GitHub Actions CI/CD Workflow Parser.
"""

from pathlib import Path
import pytest
from repograph.parsers.cicd.github_actions import GitHubActionsParser


def test_github_actions_parser(sample_repo_path):
    parser = GitHubActionsParser()
    wf_file = sample_repo_path / ".github" / "workflows" / "deploy.yml"
    rel_path = ".github/workflows/deploy.yml"
    content = wf_file.read_text()

    assert parser.can_parse(wf_file, rel_path) is True
    results = parser.parse(wf_file, rel_path, content)

    node_names = [node.name for node, _ in results]
    assert "Production Deployment Pipeline" in node_names
    assert "actions/checkout@v4" in node_names
    assert "untrusted-vendor/custom-deploy@master" in node_names
    assert "Secret: PROD_API_KEY" in node_names
    assert "Secret: DB_PASSWORD" in node_names

    # Check third party unpinned action metadata
    untrusted_node = next(n for n, _ in results if n.name == "untrusted-vendor/custom-deploy@master")
    assert untrusted_node.metadata["is_third_party"] is True
    assert untrusted_node.metadata["is_pinned_sha"] is False
