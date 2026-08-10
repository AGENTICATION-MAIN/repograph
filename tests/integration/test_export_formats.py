"""
Integration tests for Export formats (JSON, Markdown, Mermaid, DOT).
"""

import json
from pathlib import Path
import pytest
from repograph.graph.export import GraphExporter
from repograph.reporting.formatter_json import JsonFormatter
from repograph.reporting.formatter_markdown import MarkdownFormatter


def test_markdown_report_formatting(sample_graph):
    graph, summary = sample_graph
    from repograph.risk.engine import RiskEngine
    findings = RiskEngine().analyze_graph(graph, summary)

    md = MarkdownFormatter.format(summary, graph, findings)
    assert "# Repograph Software Supply-Chain Report" in md
    assert "Executive Summary" in md
    assert "Risk Findings Breakdown" in md


def test_json_report_formatting(sample_graph):
    graph, summary = sample_graph
    from repograph.risk.engine import RiskEngine
    findings = RiskEngine().analyze_graph(graph, summary)

    json_str = JsonFormatter.format(summary, graph, findings)
    parsed = json.loads(json_str)
    assert "summary" in parsed
    assert "findings" in parsed
    assert "graph" in parsed


def test_mermaid_and_dot_exports(sample_graph):
    graph, _ = sample_graph
    mermaid_str = GraphExporter.to_mermaid(graph)
    dot_str = GraphExporter.to_dot(graph)

    assert mermaid_str.startswith("graph TD")
    assert "digraph RepositoryGraph" in dot_str
