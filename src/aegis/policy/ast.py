"""
Abstract Syntax Tree (AST) definitions for Aegis Policy DSL.

Provides symbolic expression nodes for deterministic policy evaluation.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Union


class ASTNode(ABC):
    """Base class for all AST expression nodes."""

    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> Any:
        """Evaluates node against execution context dictionary."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serializes AST node to dict."""
        pass


@dataclass
class Literal(ASTNode):
    """Constant literal value (int, float, str, bool, list, dict, None)."""
    value: Any

    def evaluate(self, context: Dict[str, Any]) -> Any:
        return self.value

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "Literal", "value": self.value}


@dataclass
class FieldPath(ASTNode):
    """Resolves dot-separated field paths from context (e.g. 'args.amount', 'agent.id')."""
    path: str

    def evaluate(self, context: Dict[str, Any]) -> Any:
        parts = self.path.split(".")
        curr = context
        for part in parts:
            if isinstance(curr, dict):
                curr = curr.get(part)
            elif hasattr(curr, part):
                curr = getattr(curr, part)
            else:
                return None
            if curr is None:
                return None
        return curr

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "FieldPath", "path": self.path}


@dataclass
class BinaryOp(ASTNode):
    """Binary operation node supporting arithmetic and comparison."""
    op: str  # '+', '-', '*', '/', '%', '==', '!=', '<', '<=', '>', '>=', 'in', 'contains', 'matches', 'starts_with', 'ends_with'
    left: ASTNode
    right: ASTNode

    def evaluate(self, context: Dict[str, Any]) -> Any:
        lval = self.left.evaluate(context)
        rval = self.right.evaluate(context)

        # Comparisons
        if self.op == "==":
            return lval == rval
        elif self.op == "!=":
            return lval != rval
        elif self.op == "<":
            if lval is None or rval is None:
                return False
            return lval < rval
        elif self.op == "<=":
            if lval is None or rval is None:
                return False
            return lval <= rval
        elif self.op == ">":
            if lval is None or rval is None:
                return False
            return lval > rval
        elif self.op == ">=":
            if lval is None or rval is None:
                return False
            return lval >= rval
        elif self.op == "in":
            if rval is None:
                return False
            if isinstance(rval, (list, tuple, set, dict, str)):
                return lval in rval
            return False
        elif self.op == "contains":
            if lval is None:
                return False
            if isinstance(lval, (list, tuple, set, dict, str)):
                return rval in lval
            return False
        elif self.op == "matches":
            if lval is None or rval is None:
                return False
            return bool(re.search(str(rval), str(lval)))
        elif self.op == "starts_with":
            if lval is None or rval is None:
                return False
            return str(lval).startswith(str(rval))
        elif self.op == "ends_with":
            if lval is None or rval is None:
                return False
            return str(lval).endswith(str(rval))

        # Arithmetic
        elif self.op == "+":
            return (lval or 0) + (rval or 0)
        elif self.op == "-":
            return (lval or 0) - (rval or 0)
        elif self.op == "*":
            return (lval or 0) * (rval or 0)
        elif self.op == "/":
            if rval == 0 or rval is None:
                return 0.0
            return (lval or 0) / rval
        elif self.op == "%":
            if rval == 0 or rval is None:
                return 0
            return (lval or 0) % rval

        raise ValueError(f"Unsupported binary operator '{self.op}'")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "BinaryOp",
            "op": self.op,
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
        }


@dataclass
class UnaryOp(ASTNode):
    """Unary operation node (e.g. 'not', 'neg', 'is_null', 'is_not_null')."""
    op: str  # 'not', '-', 'is_null', 'is_not_null'
    operand: ASTNode

    def evaluate(self, context: Dict[str, Any]) -> Any:
        val = self.operand.evaluate(context)
        if self.op == "not":
            return not bool(val)
        elif self.op == "-":
            return -val if val is not None else 0
        elif self.op == "is_null":
            return val is None
        elif self.op == "is_not_null":
            return val is not None
        raise ValueError(f"Unsupported unary operator '{self.op}'")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "UnaryOp",
            "op": self.op,
            "operand": self.operand.to_dict(),
        }


@dataclass
class LogicalOp(ASTNode):
    """Multi-child logical operator (AND, OR)."""
    op: str  # 'AND', 'OR'
    operands: List[ASTNode]

    def evaluate(self, context: Dict[str, Any]) -> bool:
        if self.op.upper() == "AND":
            for child in self.operands:
                if not bool(child.evaluate(context)):
                    return False
            return True
        elif self.op.upper() == "OR":
            for child in self.operands:
                if bool(child.evaluate(context)):
                    return True
            return False
        raise ValueError(f"Unsupported logical operator '{self.op}'")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "LogicalOp",
            "op": self.op,
            "operands": [c.to_dict() for c in self.operands],
        }


@dataclass
class FunctionCall(ASTNode):
    """Deterministic built-in function invocation."""
    func_name: str
    args: List[ASTNode]

    def evaluate(self, context: Dict[str, Any]) -> Any:
        from aegis.policy.stdlib import STDLIB_FUNCTIONS
        evaluated_args = [arg.evaluate(context) for arg in self.args]
        if self.func_name not in STDLIB_FUNCTIONS:
            raise ValueError(f"Unknown standard library function '{self.func_name}'")
        return STDLIB_FUNCTIONS[self.func_name](*evaluated_args)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "FunctionCall",
            "func_name": self.func_name,
            "args": [a.to_dict() for a in self.args],
        }
