"""
Dynamic Taint and Information Flow Tracking Engine for AegisKernel.

Tracks data origins, untrusted injections, and information flow across multi-step agent reasoning.
"""

from __future__ import annotations

import logging
import re
import threading
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from aegis.core.exceptions import TaintViolationError
from aegis.core.types import (
    InvariantViolation,
    Severity,
    TaintLevel,
    TaintTag,
    ToolExecutionIntent,
)
from aegis.taint.rules import DEFAULT_SINK_RULES, TaintSinkRule

logger = logging.getLogger("aegis.taint")


class TaintTracker:
    """
    Thread-Safe Dynamic Taint & Information Flow Tracker.
    Maintains provenance state across sessions and verifies sink constraints.
    """

    def __init__(self, sink_rules: Optional[List[TaintSinkRule]] = None):
        self._session_taint: Dict[str, Dict[str, TaintTag]] = {}
        self._sink_rules: Dict[Tuple[str, str], TaintSinkRule] = {}
        self._lock = threading.RLock()

        rules = sink_rules if sink_rules is not None else DEFAULT_SINK_RULES
        for rule in rules:
            self._sink_rules[(rule.tool_name, rule.parameter_name)] = rule

    def register_sink_rule(self, rule: TaintSinkRule) -> None:
        """Registers a sink restriction rule."""
        with self._lock:
            self._sink_rules[(rule.tool_name, rule.parameter_name)] = rule

    def ingest_data(
        self,
        session_id: str,
        key: str,
        level: TaintLevel,
        source: str,
        provenance_path: Optional[List[str]] = None,
    ) -> TaintTag:
        """Records a new input or ingested piece of data into session taint memory."""
        tag = TaintTag(
            level=level,
            source=source,
            timestamp=time.time(),
            provenance_path=list(provenance_path or [source]),
            sanitized=False,
        )
        with self._lock:
            if session_id not in self._session_taint:
                self._session_taint[session_id] = {}
            self._session_taint[session_id][key] = tag
        return tag

    def sanitize_key(
        self,
        session_id: str,
        key: str,
        sanitizer_name: str,
        new_level: Optional[TaintLevel] = None,
    ) -> Optional[TaintTag]:
        """Marks a session key as sanitized by a verified sanitizer."""
        with self._lock:
            if session_id in self._session_taint and key in self._session_taint[session_id]:
                tag = self._session_taint[session_id][key]
                tag.sanitized = True
                tag.sanitizer_name = sanitizer_name
                if new_level is not None:
                    tag.level = new_level
                tag.provenance_path.append(f"sanitizer:{sanitizer_name}")
                return tag
            return None

    def get_session_taint(self, session_id: str) -> Dict[str, TaintTag]:
        """Retrieves all tracked taint tags for a session."""
        with self._lock:
            return dict(self._session_taint.get(session_id, {}))

    def compute_intent_taint(
        self,
        intent: ToolExecutionIntent,
    ) -> Dict[str, TaintTag]:
        """
        Determines the taint tags for each argument in an intent based on session history
        and explicit taint maps.
        """
        session_tags = self.get_session_taint(intent.session_id)
        effective_taint: Dict[str, TaintTag] = {}

        for param_name, param_val in intent.arguments.items():
            # If explicit taint tag was provided in intent, use it
            if param_name in intent.taint_map:
                effective_taint[param_name] = intent.taint_map[param_name]
                continue

            # If parameter matches a known session taint key, inherit it
            if param_name in session_tags:
                effective_taint[param_name] = session_tags[param_name]
                continue

            # Scan strings in parameter for any indirect injection patterns or keywords
            if isinstance(param_val, str):
                if any(x in param_val.lower() for x in ["ignore previous instructions", "system override", "jailbreak", "<script>"]):
                    effective_taint[param_name] = TaintTag(
                        level=TaintLevel.MALICIOUS_ADVERSARIAL,
                        source="pattern_scanner:heuristic_injection",
                        sanitized=False,
                    )
                    continue

            # Check if entire session has ingested untrusted external data
            highest_session_taint = TaintLevel.SYSTEM
            for t_tag in session_tags.values():
                if t_tag.level.value > highest_session_taint.value:
                    highest_session_taint = t_tag.level

            effective_taint[param_name] = TaintTag(
                level=highest_session_taint,
                source=f"session_inferred:{intent.session_id}",
                sanitized=False,
            )

        return effective_taint

    def verify_intent_taint_safety(
        self,
        intent: ToolExecutionIntent,
    ) -> List[InvariantViolation]:
        """
        Verifies that no argument in the execution intent violates protected sink constraints.
        Returns list of violations.
        """
        violations: List[InvariantViolation] = []
        effective_taints = self.compute_intent_taint(intent)

        for param_name, taint_tag in effective_taints.items():
            sink_rule = self._sink_rules.get((intent.tool_name, param_name))
            if not sink_rule:
                # Check wildcard tool rule
                sink_rule = self._sink_rules.get(("*", param_name))

            if sink_rule:
                if sink_rule.is_violated(
                    current_taint=taint_tag.level,
                    is_sanitized=taint_tag.sanitized,
                    sanitizer=taint_tag.sanitizer_name,
                ):
                    violations.append(
                        InvariantViolation(
                            rule_id=f"TAINT_SINK_{intent.tool_name}_{param_name}",
                            rule_name=f"Taint Sink Breach: {intent.tool_name}.{param_name}",
                            severity=Severity.CRITICAL,
                            message=(
                                f"Tainted data of level '{taint_tag.level.name}' from source '{taint_tag.source}' "
                                f"attempted to flow into protected sink '{intent.tool_name}.{param_name}' "
                                f"(max allowed: '{sink_rule.max_allowed_taint.name}')."
                            ),
                            field_name=param_name,
                            expected_condition=f"taint <= {sink_rule.max_allowed_taint.name} or sanitized",
                            actual_value=taint_tag.level.name,
                            remediation_suggestion=(
                                f"Pass data through an approved sanitizer ({', '.join(sink_rule.allowed_sanitizers) or 'any'}) "
                                f"before passing to '{intent.tool_name}'."
                            ),
                        )
                    )

        return violations

    def clear_session(self, session_id: str) -> None:
        """Clears taint tracking data for a session."""
        with self._lock:
            self._session_taint.pop(session_id, None)
