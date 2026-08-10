"""
Unit tests for Source Import Parsers.
"""

from pathlib import Path
import pytest
from repograph.parsers.imports.js_ts_imports import JavaScriptImportParser
from repograph.parsers.imports.python_imports import PythonImportParser


def test_python_ast_import_parser(sample_repo_path):
    parser = PythonImportParser()
    app_file = sample_repo_path / "src" / "app.py"
    content = app_file.read_text()

    assert parser.can_parse(app_file, "src/app.py") is True
    results = parser.parse(app_file, "src/app.py", content)

    imported_names = [node.name for node, _ in results]
    assert "requests" in imported_names
    assert "fastapi" in imported_names
    assert ".auth" in imported_names
    assert ".database" in imported_names


def test_js_ts_import_parser(sample_repo_path):
    parser = JavaScriptImportParser()
    js_file = sample_repo_path / "frontend" / "index.js"
    content = js_file.read_text()

    assert parser.can_parse(js_file, "frontend/index.js") is True
    results = parser.parse(js_file, "frontend/index.js", content)

    imported_names = [node.name for node, _ in results]
    assert "express" in imported_names
    assert "./api" in imported_names
