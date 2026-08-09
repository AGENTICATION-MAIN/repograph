"""
AegisKernel Telemetry and Operational Metrics.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Any, Dict, List


class TelemetryCollector:
    """
    In-memory metrics and telemetry aggregator for AegisKernel.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self.start_time = time.time()
        self.total_evaluations = 0
        self.decision_counts: Dict[str, int] = defaultdict(int)
        self.violations_by_rule: Dict[str, int] = defaultdict(int)
        self.threats_detected = 0
        self.taint_breaches = 0
        self.total_latency_ms = 0.0

    def record_verification(
        self,
        decision: str,
        latency_ms: float,
        violations: List[Any],
    ) -> None:
        """Records a completed verification event."""
        with self._lock:
            self.total_evaluations += 1
            self.decision_counts[decision] += 1
            self.total_latency_ms += latency_ms

            for v in violations:
                rule_id = getattr(v, "rule_id", "unknown")
                self.violations_by_rule[rule_id] += 1
                if "THR_" in rule_id or "ADVERSARIAL" in rule_id:
                    self.threats_detected += 1
                if "TAINT_" in rule_id:
                    self.taint_breaches += 1

    def get_summary(self) -> Dict[str, Any]:
        """Returns snapshot of telemetry metrics."""
        with self._lock:
            uptime = time.time() - self.start_time
            avg_lat = (self.total_latency_ms / self.total_evaluations) if self.total_evaluations > 0 else 0.0
            return {
                "uptime_seconds": round(uptime, 2),
                "total_evaluations": self.total_evaluations,
                "decisions": dict(self.decision_counts),
                "average_latency_ms": round(avg_lat, 3),
                "threats_detected": self.threats_detected,
                "taint_breaches": self.taint_breaches,
                "top_violations": dict(
                    sorted(self.violations_by_rule.items(), key=lambda x: x[1], reverse=True)[:10]
                ),
            }


GLOBAL_TELEMETRY = TelemetryCollector()
