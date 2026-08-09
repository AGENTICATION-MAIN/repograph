"""
Shadow State Sandbox for AegisKernel.

Executes proposed tool mutations against an isolated memory state snapshot,
verifies formal invariants, and computes differential change sets before execution.
"""

from __future__ import annotations

import copy
import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

from aegis.core.exceptions import SandboxSimulationError
from aegis.core.types import InvariantViolation, ToolExecutionIntent
from aegis.simulation.invariants import DEFAULT_STATE_INVARIANTS, StateInvariant

logger = logging.getLogger("aegis.simulation")


class ShadowSandbox:
    """
    Thread-Safe Pre-Flight Simulation Sandbox.
    Simulates mutations on shadow state copies to verify state invariants before committing.
    """

    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        self._state: Dict[str, Any] = copy.deepcopy(initial_state or {})
        self._invariants: Dict[str, StateInvariant] = {}
        self._handlers: Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]] = {}
        self._lock = threading.RLock()

        for inv in DEFAULT_STATE_INVARIANTS:
            self._invariants[inv.invariant_id] = inv

    def register_invariant(self, invariant: StateInvariant) -> None:
        """Registers a state invariant."""
        with self._lock:
            self._invariants[invariant.invariant_id] = invariant

    def register_tool_simulation_handler(
        self,
        tool_name: str,
        handler: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        """
        Registers a shadow mutation handler for a tool.
        handler signature: (current_state, tool_arguments) -> mutated_state
        """
        with self._lock:
            self._handlers[tool_name] = handler

    def get_state_snapshot(self) -> Dict[str, Any]:
        """Returns deep copy of current state."""
        with self._lock:
            return copy.deepcopy(self._state)

    def set_state(self, new_state: Dict[str, Any]) -> None:
        """Updates the committed state."""
        with self._lock:
            self._state = copy.deepcopy(new_state)

    def compute_diff(self, pre_state: Dict[str, Any], post_state: Dict[str, Any]) -> Dict[str, Any]:
        """Computes structural difference between pre and post state."""
        diff: Dict[str, Any] = {"modified": {}, "added": {}, "deleted": []}

        # Check modifications and additions
        for key, post_val in post_state.items():
            if key not in pre_state:
                diff["added"][key] = post_val
            elif pre_state[key] != post_val:
                diff["modified"][key] = {"old": pre_state[key], "new": post_val}

        # Check deletions
        for key in pre_state:
            if key not in post_state:
                diff["deleted"].append(key)

        return diff

    def simulate_and_verify(
        self,
        intent: ToolExecutionIntent,
    ) -> Tuple[bool, List[InvariantViolation], Dict[str, Any], Dict[str, Any]]:
        """
        Simulates the tool execution against an isolated shadow copy of the state.
        Returns: (success: bool, violations: List[InvariantViolation], diff: Dict, simulated_state: Dict)
        """
        with self._lock:
            pre_state = copy.deepcopy(self._state)

        # If a specific simulation handler is registered, execute it on shadow copy
        if intent.tool_name in self._handlers:
            try:
                simulated_state = self._handlers[intent.tool_name](pre_state, intent.arguments)
            except Exception as e:
                logger.error(f"Simulation handler failed for {intent.tool_name}: {str(e)}")
                violation = InvariantViolation(
                    rule_id="SIMULATION_EXECUTION_ERROR",
                    rule_name="Shadow Simulation Exception",
                    severity=Severity.CRITICAL,
                    message=f"Simulation handler failed: {str(e)}",
                )
                return False, [violation], {}, pre_state
        else:
            # Default simulation: if tool updates a record or balance, apply heuristic state update
            simulated_state = copy.deepcopy(pre_state)
            if intent.tool_name == "update_account_balance":
                acc_id = intent.arguments.get("account_id")
                delta = intent.arguments.get("amount", 0.0)
                if "accounts" not in simulated_state:
                    simulated_state["accounts"] = {}
                if acc_id not in simulated_state["accounts"]:
                    simulated_state["accounts"][acc_id] = {"balance": 1000.0}
                simulated_state["accounts"][acc_id]["balance"] += delta

            elif intent.tool_name == "delete_record":
                rec_id = intent.arguments.get("record_id")
                if "records" in simulated_state and rec_id in simulated_state["records"]:
                    del simulated_state["records"][rec_id]

        # Verify all registered state invariants
        violations: List[InvariantViolation] = []
        with self._lock:
            invariants = list(self._invariants.values())

        for inv in invariants:
            viol = inv.verify(pre_state, simulated_state)
            if viol:
                violations.append(viol)

        diff = self.compute_diff(pre_state, simulated_state)
        success = (len(violations) == 0)
        return success, violations, diff, simulated_state

    def commit_state(self, new_state: Dict[str, Any]) -> None:
        """Commits verified shadow state to live state."""
        with self._lock:
            self._state = copy.deepcopy(new_state)
