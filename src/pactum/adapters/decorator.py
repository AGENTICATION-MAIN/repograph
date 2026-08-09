"""
Python Function Guard Decorators for Pactum Leases.
"""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, Optional

from pactum.engine.kernel import PactumKernel


def pactum_barter_guard(
    kernel: PactumKernel,
    lease_id_provider: Callable[..., str],
    cost_amount: float = 1.0,
):
    """
    Decorator that meters function calls against an active Pactum capability lease.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lease_id = lease_id_provider(*args, **kwargs)
            return kernel.execute_with_leased_capability(
                lease_id=lease_id,
                operation=lambda: func(*args, **kwargs),
                cost=cost_amount,
            )
        return wrapper
    return decorator
