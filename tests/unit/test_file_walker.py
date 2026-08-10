"""
Unit tests for FileWalker and IgnoreMatcher.
"""

from pathlib import Path
import pytest
from repograph.scanner.file_walker import FileWalker
from repograph.scanner.ignore_rules import IgnoreMatcher
from repograph.scanner.metadata_collector import collect_file_metadata, detect_language


def test_ignore_matcher(tmp_path):
    # Create test .gitignore
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.log\ncustom_build/\n")

    matcher = IgnoreMatcher(tmp_path)
    assert matcher.should_ignore_dir(".git", ".git") is True
    assert matcher.should_ignore_dir("node_modules", "node_modules") is True
    assert matcher.should_ignore_dir("custom_build", "custom_build") is True
    assert matcher.should_ignore_dir("src", "src") is False

    assert matcher.should_ignore_file("app.log", "logs/app.log") is True
    assert matcher.should_ignore_file("app.pyc", "src/app.pyc") is True
    assert matcher.should_ignore_file("app.py", "src/app.py") is False


def test_file_walker_traversal(sample_repo_path):
    walker = FileWalker(sample_repo_path)
    files = list(walker.walk())
    rel_paths = [rel for _, rel, _ in files]

    assert "package.json" in rel_paths
    assert "requirements.txt" in rel_paths
    assert "go.mod" in rel_paths
    assert "src/app.py" in rel_paths
    assert ".github/workflows/deploy.yml" in rel_paths


def test_metadata_collection(sample_repo_path):
    py_file = sample_repo_path / "src" / "app.py"
    meta = collect_file_metadata(py_file)

    assert meta["language"] == "Python"
    assert meta["line_count"] > 0
    assert len(meta["sha256"]) == 64
