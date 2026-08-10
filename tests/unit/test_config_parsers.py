"""
Unit tests for Configuration and Docker Parsers.
"""

from pathlib import Path
import pytest
from repograph.parsers.config.docker_parser import DockerConfigParser
from repograph.parsers.config.env_parser import EnvConfigParser


def test_env_config_parser(sample_repo_path):
    parser = EnvConfigParser()
    env_file = sample_repo_path / ".env.example"
    content = env_file.read_text()

    assert parser.can_parse(env_file, ".env.example") is True
    results = parser.parse(env_file, ".env.example", content)

    var_names = [node.name for node, _ in results]
    assert "DATABASE_URL" in var_names
    assert "STRIPE_API_KEY" in var_names

    # Check secret detection metadata
    stripe_node = next(node for node, _ in results if node.name == "STRIPE_API_KEY")
    assert stripe_node.metadata["is_plaintext_secret"] is True


def test_docker_config_parser(sample_repo_path):
    parser = DockerConfigParser()
    dockerfile = sample_repo_path / "Dockerfile"
    compose_file = sample_repo_path / "docker-compose.yml"

    assert parser.can_parse(dockerfile, "Dockerfile") is True
    assert parser.can_parse(compose_file, "docker-compose.yml") is True

    # Parse Dockerfile
    df_results = parser.parse(dockerfile, "Dockerfile", dockerfile.read_text())
    df_names = [node.name for node, _ in df_results]
    assert "python:latest" in df_names

    # Check unpinned image detection
    py_node = next(node for node, _ in df_results if node.name == "python:latest")
    assert py_node.metadata["is_unpinned_base"] is True

    # Parse docker-compose.yml
    compose_results = parser.parse(compose_file, "docker-compose.yml", compose_file.read_text())
    compose_names = [node.name for node, _ in compose_results]
    assert "web" in compose_names
    assert "db" in compose_names
