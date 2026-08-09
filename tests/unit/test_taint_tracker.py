"""
Unit tests for Dynamic Taint Tracking and Information Flow Control.
"""

import pytest
from aegis.core.types import TaintLevel, ToolExecutionIntent
from aegis.taint.rules import TaintSinkRule
from aegis.taint.tracker import TaintTracker


def test_taint_ingestion_and_sink_blocking():
    tracker = TaintTracker()
    session_id = "session-sec-101"

    # Ingest untrusted scraped web data
    tracker.ingest_data(
        session_id=session_id,
        key="scraped_input",
        level=TaintLevel.UNTRUSTED_EXTERNAL,
        source="web_crawler",
    )

    intent = ToolExecutionIntent(
        tool_name="execute_sql",
        arguments={"query": "SELECT * FROM secrets"},
        agent_id="agent-01",
        session_id=session_id,
    )

    # Sink rule requires max taint <= AUTHENTICATED_USER. UNTRUSTED_EXTERNAL should fail.
    violations = tracker.verify_intent_taint_safety(intent)
    assert len(violations) >= 1
    assert "TAINT_SINK_execute_sql_query" in violations[0].rule_id


def test_taint_sanitization():
    tracker = TaintTracker()
    session_id = "session-sec-102"

    tracker.ingest_data(
        session_id=session_id,
        key="query",
        level=TaintLevel.UNTRUSTED_EXTERNAL,
        source="external_api",
    )

    # Sanitize the key using approved parameterized query sanitizer
    tracker.sanitize_key(
        session_id=session_id,
        key="query",
        sanitizer_name="parameterized_query_sanitizer",
        new_level=TaintLevel.AUTHENTICATED_USER,
    )

    intent = ToolExecutionIntent(
        tool_name="execute_sql",
        arguments={"query": "SELECT * FROM orders WHERE id = ?"},
        agent_id="agent-01",
        session_id=session_id,
    )

    violations = tracker.verify_intent_taint_safety(intent)
    assert len(violations) == 0
