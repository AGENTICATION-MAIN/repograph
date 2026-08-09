"""
Dynamic Equilibrium Market Tracking and Shadow Price Discovery for Pactum.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from pactum.core.types import BargainingAgreement, ResourceType


@dataclass
class MarketEquilibriumState:
    """Snapshot of current cross-resource barter exchange ratios and liquidity."""
    timestamp: float
    total_trades_count: int
    total_social_welfare_gained: float
    # Shadow price ratio: e.g. (API_RATE_LIMIT, QUEUE_PRIORITY_SLOT) -> 1.0 API token = 0.4 priority slots
    shadow_exchange_rates: Dict[str, float]
    resource_volume_traded: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_trades_count": self.total_trades_count,
            "total_social_welfare_gained": round(self.total_social_welfare_gained, 4),
            "shadow_exchange_rates": self.shadow_exchange_rates,
            "resource_volume_traded": self.resource_volume_traded,
        }


class EquilibriumTracker:
    """
    Computes real-time empirical marginal exchange ratios and aggregate welfare.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._agreements: List[BargainingAgreement] = []
        self._volume_by_resource: Dict[ResourceType, float] = defaultdict(float)
        self._pair_trade_ratios: Dict[Tuple[ResourceType, ResourceType], List[float]] = defaultdict(list)
        self._total_welfare = 0.0

    def record_agreement(self, agreement: BargainingAgreement) -> None:
        with self._lock:
            self._agreements.append(agreement)
            self._volume_by_resource[agreement.resource_a_to_b_type] += agreement.quantity_a_to_b
            self._volume_by_resource[agreement.resource_b_to_a_type] += agreement.quantity_b_to_a

            if agreement.quantity_b_to_a > 0:
                ratio_a_to_b = agreement.quantity_a_to_b / agreement.quantity_b_to_a
                pair = (agreement.resource_a_to_b_type, agreement.resource_b_to_a_type)
                self._pair_trade_ratios[pair].append(ratio_a_to_b)

            welfare = agreement.surplus_utility_a + agreement.surplus_utility_b
            self._total_welfare += welfare

    def get_equilibrium_snapshot(self) -> MarketEquilibriumState:
        with self._lock:
            rates = {}
            for (r_a, r_b), ratios in self._pair_trade_ratios.items():
                if ratios:
                    # Exponential moving average / recent average
                    recent = ratios[-10:]
                    avg_rate = sum(recent) / len(recent)
                    key = f"{r_a.value}:{r_b.value}"
                    rates[key] = round(avg_rate, 4)

            vol_dict = {r.value: round(v, 2) for r, v in self._volume_by_resource.items()}

            return MarketEquilibriumState(
                timestamp=time.time(),
                total_trades_count=len(self._agreements),
                total_social_welfare_gained=self._total_welfare,
                shadow_exchange_rates=rates,
                resource_volume_traded=vol_dict,
            )
