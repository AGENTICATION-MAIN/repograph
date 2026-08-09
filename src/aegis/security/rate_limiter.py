"""
Sliding Window Rate Limiter & Velocity Controller for AegisKernel.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Dict, Optional, Tuple


class SlidingWindowRateLimiter:
    """
    Thread-Safe Sliding Window Rate Limiter.
    Enforces per-agent, per-session, and per-tool call velocity limits.
    """

    def __init__(self, default_limit_per_minute: int = 120):
        self.default_limit_per_minute = default_limit_per_minute
        self._windows: Dict[str, deque] = {}
        self._lock = threading.RLock()

    def check_and_record(
        self,
        key: str,
        limit_per_minute: Optional[int] = None,
        now: Optional[float] = None,
    ) -> Tuple[bool, int, float]:
        """
        Checks if key is within rate limit and records current call.
        Returns: (allowed: bool, current_count: int, retry_after_seconds: float)
        """
        curr_time = now if now is not None else time.time()
        limit = limit_per_minute if limit_per_minute is not None else self.default_limit_per_minute
        window_start = curr_time - 60.0

        with self._lock:
            if key not in self._windows:
                self._windows[key] = deque()

            window = self._windows[key]

            # Evict timestamps older than 60 seconds
            while window and window[0] < window_start:
                window.popleft()

            count = len(window)
            if count >= limit:
                oldest_in_window = window[0]
                retry_after = max(0.1, 60.0 - (curr_time - oldest_in_window))
                return False, count, round(retry_after, 2)

            window.append(curr_time)
            return True, count + 1, 0.0

    def reset(self, key: Optional[str] = None) -> None:
        """Resets rate limit counter for a specific key or all keys."""
        with self._lock:
            if key:
                self._windows.pop(key, None)
            else:
                self._windows.clear()
