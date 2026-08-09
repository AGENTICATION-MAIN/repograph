"""
OpenAI Tool Calling Adapter for AegisKernel.

Intercepts and guards standard OpenAI chat.completions function/tool calling objects.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple, Union

from aegis.adapters.base import BaseAgentAdapter
from aegis.core.kernel import AegisKernel
from aegis.core.types import Decision, ToolExecutionIntent, VerificationResult


class OpenAIToolAdapter(BaseAgentAdapter):
    """
    Guards OpenAI tool calling structures.
    """

    def parse_tool_call(self, tool_call_dict: Dict[str, Any], agent_id: str, session_id: str, capability_token_id: Optional[str] = None) -> ToolExecutionIntent:
        """Parses OpenAI tool_call schema into Aegis ToolExecutionIntent."""
        call_id = tool_call_dict.get("id", "openai-call")
        function_spec = tool_call_dict.get("function", {})
        tool_name = function_spec.get("name", "")
        args_raw = function_spec.get("arguments", "{}")

        if isinstance(args_raw, str):
            try:
                arguments = json.loads(args_raw)
            except json.JSONDecodeError:
                arguments = {"__raw_invalid_json__": args_raw}
        elif isinstance(args_raw, dict):
            arguments = args_raw
        else:
            arguments = {}

        return ToolExecutionIntent(
            intent_id=call_id,
            tool_name=tool_name,
            arguments=arguments,
            agent_id=agent_id,
            session_id=session_id,
            capability_token_id=capability_token_id,
            metadata={"source": "openai_tool_call"},
        )

    def intercept_and_verify(
        self,
        raw_tool_call: Dict[str, Any],
        agent_id: str,
        session_id: str,
        capability_token_id: Optional[str] = None,
        session_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[VerificationResult, Optional[Dict[str, Any]]]:
        """
        Verifies OpenAI tool call.
        If ALLOWED: returns verification result and original or sanitized tool call.
        If DENIED/QUARANTINED: returns verification result and synthetic error tool message.
        """
        intent = self.parse_tool_call(
            raw_tool_call,
            agent_id=agent_id,
            session_id=session_id,
            capability_token_id=capability_token_id,
        )

        result = self.kernel.verify_intent(intent, session_context=session_context)

        if result.is_allowed:
            # If arguments were sanitized/degraded, return updated tool call
            if result.sanitized_arguments is not None:
                updated_call = dict(raw_tool_call)
                updated_call["function"] = {
                    "name": intent.tool_name,
                    "arguments": json.dumps(result.sanitized_arguments),
                }
                return result, updated_call
            return result, raw_tool_call

        # Return synthetic OpenAI tool response representing rejection
        tool_msg = {
            "role": "tool",
            "tool_call_id": raw_tool_call.get("id", ""),
            "name": intent.tool_name,
            "content": json.dumps({
                "status": "REJECTED_BY_AEGIS_KERNEL",
                "decision": result.decision.value,
                "reason": result.reason,
                "violations": [v.to_dict() for v in result.violations],
            }),
        }
        return result, tool_msg
