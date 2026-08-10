"""
Unit tests for Deterministic Risk Scoring Engine.
"""

import pytest
from repograph.core.types import Severity
from repograph.risk.engine import RiskEngine


def test_risk_engine_deterministic_findings(sample_graph):
    graph, summary = sample_graph
    risk_engine = RiskEngine()
    findings = risk_engine.analyze_graph(graph, summary)

    assert len(findings) > 0
    rule_ids = [f.rule_id for f in findings]

    # Rule 1: pull_request_target secret access (CRITICAL)
    assert "RULE_CICD_PULL_REQUEST_TARGET_SECRET_EXPOSURE" in rule_ids
    crit_finding = next(f for f in findings if f.rule_id == "RULE_CICD_PULL_REQUEST_TARGET_SECRET_EXPOSURE")
    assert crit_finding.severity == Severity.CRITICAL
    assert crit_finding.risk_score >= 90.0

    # Rule 2: Unpinned 3rd-party GitHub action (HIGH)
    assert "RULE_UNPINNED_THIRD_PARTY_ACTION" in rule_ids

    # Rule 3: Unpinned Docker base image (MEDIUM)
    assert "RULE_UNPINNED_DOCKER_BASE" in rule_ids

    # Rule 4: Plaintext secret in .env (HIGH)
    assert "RULE_PLAINTEXT_SECRET_IN_CONFIG" in rule_ids

    # Rule 5: Circular dependency loop (MEDIUM)
    assert "RULE_CIRCULAR_DEPENDENCY_CYCLE" in rule_ids

    # Summary checks
    assert summary.findings_count_by_severity[Severity.CRITICAL.value] >= 1
    assert summary.aggregate_risk_score > 50.0
