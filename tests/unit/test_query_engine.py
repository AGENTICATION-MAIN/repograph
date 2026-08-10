"""
Unit tests for Query Engine and Finding Explanations.
"""

import pytest
from repograph.query.query_engine import QueryEngine
from repograph.risk.engine import RiskEngine


def test_query_engine_explain_finding(sample_graph):
    graph, summary = sample_graph
    risk_engine = RiskEngine()
    findings = risk_engine.analyze_graph(graph, summary)

    query_engine = QueryEngine(graph, findings)
    target_finding = findings[0]

    explanation = query_engine.explain_finding(target_finding.finding_id)
    assert explanation["finding"]["title"] == target_finding.title
    assert explanation["evidence_count"] > 0
    assert len(explanation["affected_topology"]) > 0


def test_query_dependents(sample_graph):
    graph, summary = sample_graph
    query_engine = QueryEngine(graph)

    res = query_engine.query_dependents("fastapi")
    assert len(res) >= 1
    assert res[0]["total_direct_dependents"] >= 1
