"""
Python Function Guard Decorator for AegisKernel.
"""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, Dict, Optional

from aegis.core.exceptions import InvariantBreachError
from aegis.core.kernel import AegisKernel
from aegis.core.types import ToolExecutionIntent, VerificationResult


def aegis_guard(
    kernel: AegisKernel,
    tool_name: Optional[str] = None,
    agent_id: str = "default-agent",
    session_id: str = "default-session",
    raise_on_deny: bool = True,
):
    """
    Decorator that attaches AegisKernel verification to any Python tool function.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        target_tool_name = tool_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Bind arguments to function signature
            sig = inspect.signature(func)
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            call_kwargs = bound.arguments

            # Extract optional aegis session context from kwargs if present
            session_ctx = call_kwargs.pop("__aegis_session_ctx__", None)
            cap_token = call_kwargs.pop("__aegis_capability_token__", None)

            intent = ToolExecutionIntent(
                tool_name=target_tool_name,
                arguments=call_kwargs,
                agent_id=agent_id,
                session_id=session_id,
                capability_token_id=cap_token,
            )

            result, output = kernel.execute_guarded(
                intent=intent,
                tool_callable=lambda **kw: func(**kw),
                session_context=session_ctx,
            )

            if not result.is_allowed:
                if raise_on_deny:
                    raise InvariantBreachError(
                        f"AegisKernel execution denied for '{target_tool_name}': {result.reason}",
                        violations=[v.to_dict() for v in result.violations],
                    )
                return {
                    "error": "AEGIS_EXECUTION_DENIED",
                    "decision": result.decision.value,
                    "reason": result.reason,
                }

            return output

        return wrapper
    return decorator
