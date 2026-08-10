"""
Unit tests for Dependency Manifest Parsers (Python, Node.js, Go, Rust).
"""

from pathlib import Path
import pytest
from repograph.parsers.dependencies.go_parser import GoDependencyParser
from repograph.parsers.dependencies.node_parser import NodeDependencyParser
from repograph.parsers.dependencies.python_parser import PythonDependencyParser
from repograph.parsers.dependencies.rust_parser import RustDependencyParser


def test_python_requirements_parser(sample_repo_path):
    parser = PythonDependencyParser()
    req_file = sample_repo_path / "requirements.txt"
    content = req_file.read_text()

    assert parser.can_parse(req_file, "requirements.txt") is True
    results = parser.parse(req_file, "requirements.txt", content)

    dep_names = [node.name for node, _ in results]
    assert "fastapi" in dep_names
    assert "pydantic" in dep_names
    assert "requests" in dep_names
    assert "uvicorn" in dep_names


def test_node_package_json_parser(sample_repo_path):
    parser = NodeDependencyParser()
    pkg_file = sample_repo_path / "package.json"
    content = pkg_file.read_text()

    assert parser.can_parse(pkg_file, "package.json") is True
    results = parser.parse(pkg_file, "package.json", content)

    dep_names = [node.name for node, _ in results]
    assert "express" in dep_names
    assert "axios" in dep_names
    assert "lodash" in dep_names
    assert "jest" in dep_names


def test_go_mod_parser(sample_repo_path):
    parser = GoDependencyParser()
    go_file = sample_repo_path / "go.mod"
    content = go_file.read_text()

    assert parser.can_parse(go_file, "go.mod") is True
    results = parser.parse(go_file, "go.mod", content)

    dep_names = [node.name for node, _ in results]
    assert "github.com/gin-gonic/gin" in dep_names
    assert "github.com/google/uuid" in dep_names


def test_rust_cargo_parser(tmp_path):
    cargo_file = tmp_path / "Cargo.toml"
    cargo_file.write_text("""
[package]
name = "my-crate"
version = "0.1.0"

[dependencies]
serde = "1.0"
tokio = { version = "1.38", features = ["full"] }

[dev-dependencies]
criterion = "0.5"
""")
    parser = RustDependencyParser()
    assert parser.can_parse(cargo_file, "Cargo.toml") is True
    results = parser.parse(cargo_file, "Cargo.toml", cargo_file.read_text())

    dep_names = [node.name for node, _ in results]
    assert "serde" in dep_names
    assert "tokio" in dep_names
    assert "criterion" in dep_names
