"""
Integration tests for Repograph CLI commands.
"""

import json
from pathlib import Path
import pytest
from repograph.cli.main import _execute_scan, cmd_scan, main


def test_cli_scan_json_output(sample_repo_path, capsys):
    graph, summary, findings = _execute_scan(sample_repo_path)
    assert summary.total_files > 0
    assert len(findings) > 0


def test_cli_findings_structure(sample_repo_path):
    _, _, findings = _execute_scan(sample_repo_path)
    finding_dicts = [f.to_dict() for f in findings]
    assert all("finding_id" in f for f in finding_dicts)
    assert all("severity" in f for f in finding_dicts)
    assert all("evidence" in f for f in finding_dicts)
