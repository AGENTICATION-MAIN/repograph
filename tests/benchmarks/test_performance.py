"""
Performance and Latency Benchmarks for AegisKernel.
"""

import time
import pytest
from aegis.core.kernel import AegisKernel
from aegis.core.types import Decision, ToolExecutionIntent
from aegis.policy.parser import PolicyParser


def test_verification_latency_and_throughput(kernel):
    # Register 3 policy rules
    kernel.policies.register_rule(PolicyParser.parse_rule({
        "rule_id": "PERF_RULE_1",
        "rule_name": "Amount Cap",
        "phase": "PRE_EXECUTION",
        "condition": {"field": "args.amount", "op": "<=", "value": 50000},
        "target_tools": ["benchmark_tool"],
    }))

    kernel.policies.register_rule(PolicyParser.parse_rule({
        "rule_id": "PERF_RULE_2",
        "rule_name": "Currency Check",
        "phase": "PRE_EXECUTION",
        "condition": {"field": "args.currency", "op": "==", "value": "USD"},
        "target_tools": ["benchmark_tool"],
    }))

    intent = ToolExecutionIntent(
        tool_name="benchmark_tool",
        arguments={"amount": 250.0, "currency": "USD"},
        agent_id="perf-agent",
        session_id="perf-session",
    )

    # Warmup
    for _ in range(50):
        kernel.verify_intent(intent)

    # Benchmark 1,000 evaluations
    iterations = 1000
    start = time.perf_counter()
    for _ in range(iterations):
        res = kernel.verify_intent(intent)
        assert res.decision == Decision.ALLOW
    total_time = time.perf_counter() - start

    avg_latency_ms = (total_time / iterations) * 1000.0
    throughput_ops_sec = iterations / total_time

    print(f"\n[BENCHMARK] Avg Latency: {avg_latency_ms:.4f} ms | Throughput: {throughput_ops_sec:.1f} ops/sec")

    # Assert performance boundaries: average latency < 5.0ms (typically <0.3ms), throughput > 500 ops/sec
    assert avg_latency_ms < 5.0, f"Average latency too high: {avg_latency_ms} ms"
    assert throughput_ops_sec > 200, f"Throughput too low: {throughput_ops_sec} ops/sec"
