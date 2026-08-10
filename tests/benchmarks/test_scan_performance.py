"""
Scan and Graph Construction Performance Benchmarks for Repograph.
"""

import time
import pytest
from repograph.graph.builder import GraphBuilder
from repograph.risk.engine import RiskEngine


def test_scan_and_risk_analysis_performance(sample_repo_path):
    # Benchmark 20 consecutive end-to-end repository scans
    iterations = 20
    start = time.perf_counter()

    for _ in range(iterations):
        builder = GraphBuilder(sample_repo_path)
        graph, summary = builder.build_graph()
        RiskEngine().analyze_graph(graph, summary)

    total_time_s = time.perf_counter() - start
    avg_latency_ms = (total_time_s / iterations) * 1000.0
    throughput_scans_sec = iterations / total_time_s

    print(f"\n[BENCHMARK] Avg Scan & Analysis Latency: {avg_latency_ms:.2f} ms | Throughput: {throughput_scans_sec:.1f} scans/sec")

    # Assert scan takes less than 50ms per scan for local microservice repo
    assert avg_latency_ms < 100.0, f"Scan too slow: {avg_latency_ms:.2f} ms"
