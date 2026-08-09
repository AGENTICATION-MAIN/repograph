"""
Pactum Telemetry and Market Analytics.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Any, Dict, List


class MarketTelemetry:
    """
    In-memory metrics aggregator for Pactum barter transactions and Nash solving efficiency.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self.start_time = time.time()
        self.total_negotiations = 0
        self.successful_trades = 0
        self.failed_negotiations = 0
        self.total_solving_time_us = 0.0
        self.total_social_welfare = 0.0
        self.resource_traded_totals: Dict[str, float] = defaultdict(float)

    def record_trade(self, solving_time_us: float, welfare: float, res_a: str, qty_a: float, res_b: str, qty_b: float) -> None:
        with self._lock:
            self.total_negotiations += 1
            self.successful_trades += 1
            self.total_solving_time_us += solving_time_us
            self.total_social_welfare += welfare
            self.resource_traded_totals[res_a] += qty_a
            self.resource_traded_totals[res_b] += qty_b

    def record_failure(self) -> None:
        with self._lock:
            self.total_negotiations += 1
            self.failed_negotiations += 1

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            uptime = time.time() - self.start_time
            avg_solving_us = (self.total_solving_time_us / self.successful_trades) if self.successful_trades > 0 else 0.0
            return {
                "uptime_seconds": round(uptime, 2),
                "total_negotiations": self.total_negotiations,
                "successful_trades": self.successful_trades,
                "failed_negotiations": self.failed_negotiations,
                "average_solving_time_us": round(avg_solving_us, 2),
                "total_social_welfare_gained": round(self.total_social_welfare, 4),
                "resource_volume_traded": dict(self.resource_traded_totals),
            }


GLOBAL_TELEMETRY = MarketTelemetry()
