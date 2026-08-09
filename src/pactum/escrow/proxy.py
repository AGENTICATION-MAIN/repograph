"""
Capability Proxy Interceptor for Pactum.

Wraps outgoing API calls, queue insertions, and GPU invocations, transparently
routing requests through active bartered leases.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional, Tuple

from pactum.core.exceptions import LeaseExpiredError, LeaseQuotaExceededError
from pactum.core.types import ResourceType
from pactum.resources.quota import QuotaTracker

logger = logging.getLogger("pactum.proxy")


class CapabilityProxy:
    """
    Transparent execution proxy that meters request volume against active bartered capability leases.
    """

    def __init__(self, quota_tracker: QuotaTracker):
        self.quota_tracker = quota_tracker

    def execute_with_lease(
        self,
        lease_id: str,
        operation_callable: Callable[..., Any],
        cost_amount: float = 1.0,
        *args,
        **kwargs,
    ) -> Tuple[bool, Any, Dict[str, Any]]:
        """
        Consumes quota from lease and executes operation if allowed.
        Returns: (success: bool, result: Any, telemetry: Dict)
        """
        # Consume from quota tracker
        self.quota_tracker.consume(lease_id=lease_id, amount=cost_amount)

        # Execute underlying target function
        result = operation_callable(*args, **kwargs)

        lease = self.quota_tracker.get_lease(lease_id)
        telemetry = {
            "lease_id": lease_id,
            "cost_consumed": cost_amount,
            "remaining_quota": lease.allocated_quantity - lease.consumed_quantity if lease else 0.0,
        }

        return True, result, telemetry
