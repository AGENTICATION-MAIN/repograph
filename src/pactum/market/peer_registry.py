"""
Peer Service Registry & Capability Discovery for Pactum.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from pactum.core.types import ResourceType


@dataclass
class PeerService:
    """Represents a discovered microservice or autonomous agent participating in the barter mesh."""
    service_id: str
    service_name: str
    endpoint_url: str
    owned_capabilities: Set[ResourceType] = field(default_factory=set)
    needed_capabilities: Set[ResourceType] = field(default_factory=set)
    last_heartbeat: float = field(default_factory=time.time)
    reputation_score: float = 1.0                # Reliability metric [0.0 - 1.0]
    total_trades_completed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_alive(self, timeout_seconds: float = 60.0) -> bool:
        return (time.time() - self.last_heartbeat) < timeout_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_id": self.service_id,
            "service_name": self.service_name,
            "endpoint_url": self.endpoint_url,
            "owned_capabilities": [c.value for c in self.owned_capabilities],
            "needed_capabilities": [c.value for c in self.needed_capabilities],
            "last_heartbeat": self.last_heartbeat,
            "reputation_score": self.reputation_score,
            "total_trades_completed": self.total_trades_completed,
            "metadata": self.metadata,
        }


class PeerRegistry:
    """
    Thread-Safe Registry of Barter Network Peers.
    """

    def __init__(self):
        self._peers: Dict[str, PeerService] = {}
        self._lock = threading.RLock()

    def register_peer(
        self,
        service_id: str,
        service_name: str,
        endpoint_url: str = "internal://local",
        owned_capabilities: Optional[Set[ResourceType]] = None,
        needed_capabilities: Optional[Set[ResourceType]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PeerService:
        with self._lock:
            peer = PeerService(
                service_id=service_id,
                service_name=service_name,
                endpoint_url=endpoint_url,
                owned_capabilities=owned_capabilities or set(),
                needed_capabilities=needed_capabilities or set(),
                last_heartbeat=time.time(),
                metadata=metadata or {},
            )
            self._peers[service_id] = peer
            return peer

    def heartbeat(self, service_id: str) -> bool:
        with self._lock:
            if service_id in self._peers:
                self._peers[service_id].last_heartbeat = time.time()
                return True
            return False

    def get_peer(self, service_id: str) -> Optional[PeerService]:
        with self._lock:
            return self._peers.get(service_id)

    def list_peers(self, only_alive: bool = True) -> List[PeerService]:
        with self._lock:
            if only_alive:
                return [p for p in self._peers.values() if p.is_alive()]
            return list(self._peers.values())

    def update_reputation(self, service_id: str, delta: float) -> float:
        """Updates counterparty reliability score."""
        with self._lock:
            if service_id in self._peers:
                peer = self._peers[service_id]
                peer.reputation_score = max(0.0, min(1.0, peer.reputation_score + delta))
                if delta > 0:
                    peer.total_trades_completed += 1
                return peer.reputation_score
            return 0.0
