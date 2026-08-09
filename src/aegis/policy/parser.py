"""
Aegis Policy DSL Parser and Rule Model.

Parses declarative JSON/dict structures and string expressions into executable AST representations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union

from aegis.core.exceptions import PolicySyntaxError
from aegis.core.types import Decision, PolicyPhase, Severity
from aegis.policy.ast import (
    ASTNode,
    BinaryOp,
    FieldPath,
    FunctionCall,
    Literal,
    LogicalOp,
    UnaryOp,
)


@dataclass
class PolicyRule:
    """
    A single policy invariant rule evaluated during agent execution.
    """
    rule_id: str
    rule_name: str
    description: str
    phase: PolicyPhase
    condition: ASTNode
    action_on_violation: Decision = Decision.DENY
    severity: Severity = Severity.HIGH
    target_tools: Set[str] = field(default_factory=lambda: {"*"})
    remediation_suggestion: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    enabled: bool = True

    def applies_to_tool(self, tool_name: str) -> bool:
        """Checks if this rule applies to the specified tool name."""
        if not self.enabled:
            return False
        if "*" in self.target_tools:
            return True
        return tool_name in self.target_tools

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "description": self.description,
            "phase": self.phase.value,
            "condition": self.condition.to_dict(),
            "action_on_violation": self.action_on_violation.value,
            "severity": self.severity.value,
            "target_tools": sorted(list(self.target_tools)),
            "remediation_suggestion": self.remediation_suggestion,
            "tags": self.tags,
            "enabled": self.enabled,
        }


class PolicyParser:
    """
    Parses dictionary and structured JSON rule specifications into typed PolicyRule instances.
    """

    @classmethod
    def parse_expression(cls, expr_spec: Union[Dict[str, Any], ASTNode, str, int, float, bool]) -> ASTNode:
        """Recursively parses an expression dictionary into an ASTNode."""
        if isinstance(expr_spec, ASTNode):
            return expr_spec

        if isinstance(expr_spec, (int, float, bool)) or expr_spec is None:
            return Literal(expr_spec)

        if isinstance(expr_spec, str):
            # String could be a field path starting with args., session., taint., or a literal string
            if expr_spec.startswith(("args.", "session.", "agent.", "metadata.", "context.", "taint.", "result.")):
                return FieldPath(expr_spec)
            return Literal(expr_spec)

        if isinstance(expr_spec, dict):
            # Check for logical operators 'and', 'or', 'not'
            if "and" in expr_spec:
                items = expr_spec["and"]
                if not isinstance(items, list):
                    raise PolicySyntaxError("'and' operator requires a list of child expressions")
                return LogicalOp("AND", [cls.parse_expression(item) for item in items])

            if "or" in expr_spec:
                items = expr_spec["or"]
                if not isinstance(items, list):
                    raise PolicySyntaxError("'or' operator requires a list of child expressions")
                return LogicalOp("OR", [cls.parse_expression(item) for item in items])

            if "not" in expr_spec:
                return UnaryOp("not", cls.parse_expression(expr_spec["not"]))

            # Check for function call format: {"fn": "len", "args": [...]}
            if "fn" in expr_spec:
                func_name = expr_spec["fn"]
                fn_args = [cls.parse_expression(a) for a in expr_spec.get("args", [])]
                return FunctionCall(func_name, fn_args)

            # Check for standard binary comparison: {"field": "args.amount", "op": "<=", "value": 5000}
            if "field" in expr_spec and "op" in expr_spec:
                field_node = FieldPath(expr_spec["field"])
                op = expr_spec["op"]
                val_node = cls.parse_expression(expr_spec.get("value"))
                return BinaryOp(op, field_node, val_node)

            # Check for direct operator format: {"op": "==", "left": ..., "right": ...}
            if "op" in expr_spec and "left" in expr_spec and "right" in expr_spec:
                left = cls.parse_expression(expr_spec["left"])
                right = cls.parse_expression(expr_spec["right"])
                return BinaryOp(expr_spec["op"], left, right)

            # Check for literal dict
            return Literal(expr_spec)

        raise PolicySyntaxError(f"Cannot parse expression: {repr(expr_spec)}")

    @classmethod
    def parse_rule(cls, rule_dict: Dict[str, Any]) -> PolicyRule:
        """Parses a dictionary definition into a PolicyRule."""
        required = ["rule_id", "rule_name", "phase", "condition"]
        for req in required:
            if req not in rule_dict:
                raise PolicySyntaxError(f"Missing required policy rule field '{req}'")

        try:
            phase = PolicyPhase(rule_dict["phase"])
        except ValueError:
            raise PolicySyntaxError(f"Invalid policy phase: '{rule_dict['phase']}'")

        action = Decision(rule_dict.get("action_on_violation", Decision.DENY.value))
        severity = Severity(rule_dict.get("severity", Severity.HIGH.value))

        target_tools = set(rule_dict.get("target_tools", ["*"]))
        condition_node = cls.parse_expression(rule_dict["condition"])

        return PolicyRule(
            rule_id=rule_dict["rule_id"],
            rule_name=rule_dict["rule_name"],
            description=rule_dict.get("description", ""),
            phase=phase,
            condition=condition_node,
            action_on_violation=action,
            severity=severity,
            target_tools=target_tools,
            remediation_suggestion=rule_dict.get("remediation_suggestion"),
            tags=rule_dict.get("tags", []),
            enabled=rule_dict.get("enabled", True),
        )

    @classmethod
    def parse_ruleset(cls, rules_list: List[Dict[str, Any]]) -> List[PolicyRule]:
        """Parses a list of rule dictionaries into PolicyRule instances."""
        return [cls.parse_rule(r) for r in rules_list]
