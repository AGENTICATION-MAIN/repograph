"""
Pytest configuration and shared fixtures for Repograph test suite.
"""

from pathlib import Path
import pytest
from repograph.core.config import RepographConfig
from repograph.graph.builder import GraphBuilder


@pytest.fixture
def sample_repo_path():
    return Path(__file__).parent / "fixtures" / "sample_repo"


@pytest.fixture
def test_config():
    return RepographConfig(
        max_file_size_bytes=1024 * 1024,
        max_depth=15,
        follow_symlinks=False,
    )


@pytest.fixture
def sample_graph(sample_repo_path, test_config):
    builder = GraphBuilder(sample_repo_path, test_config)
    graph, summary = builder.build_graph()
    return graph, summary
