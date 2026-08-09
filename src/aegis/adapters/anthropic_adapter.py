"""
Anthropic Claude Tool Use Adapter for AegisKernel.

Intercepts and guards Anthropic tool_use content blocks.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from aegis.adapters.base import BaseAgentAdapter
from aegis.core.kernel import AegisKernel
from aegis.core.types import Decision, ToolExecutionIntent, VerificationResult


class AnthropicToolAdapter(BaseAgentAdapter):
    """
    Guards Anthropic Claude tool use structures.
    """

    def parse_tool_use(
        self,
        tool_use_block: Dict[str, Any],
        agent_id: str,
        session_id: str,
        capability_token_id: Optional[str] = None,
    ) -> ToolExecutionIntent:
        """Parses Anthropic tool_use block into Aegis ToolExecutionIntent."""
        tool_use_id = tool_use_block.get("id", "anthropic-call")
        tool_name = tool_use_block.get("name", "")
        arguments = tool_use_block.get("input", {})

        return ToolExecutionIntent(
            intent_id=tool_use_id,
            tool_name=tool_name,
            arguments=arguments if isinstance(arguments, dict) else {},
            agent_id=agent_id,
            session_id=session_id,
            capability_token_id=capability_token_id,
            metadata={"source": "anthropic_tool_use"},
        )

    def intercept_and_verify(
        self,
        raw_tool_use: Dict[str, Any],
        agent_id: str,
        session_id: str,
        capability_token_id: Optional[str] = None,
        session_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[VerificationResult, Optional[Dict[str, Any]]]:
        """
        Verifies Anthropic tool use block.
        If ALLOWED: returns verification result and tool block.
        If DENIED/QUARANTINED: returns verification result and synthetic tool_result error block.
        """
        intent = self.parse_tool_use(
            raw_tool_use,
            agent_id=agent_id,
            session_id=session_id,
            capability_token_id=capability_token_id,
        )

        result = self.kernel.verify_intent(intent, session_context=session_context)

        if result.is_allowed:
            if result.sanitized_arguments is not None:
                updated_block = dict(raw_tool_use)
                updated_block["input"] = result.sanitized_arguments
                return result, updated_block
            return result, raw_tool_use

        # Synthetic Anthropic tool_result block
        tool_result_block = {
            "type": "tool_result",
            "tool_use_id": raw_tool_use.get("id", ""),
            "is_error": True,
            "content": json.dumps({
                "status": "REJECTED_BY_AEGIS_KERNEL",
                "decision": result.decision.value,
                "reason": result.reason,
                "violations": [v.to_dict() for v in result.violations],
            }),
        }
        return result, tool_result_block
