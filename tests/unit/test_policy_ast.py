"""
Unit tests for Policy AST Nodes and Stdlib deterministic functions.
"""

import pytest
from aegis.policy.ast import (
    BinaryOp,
    FieldPath,
    FunctionCall,
    Literal,
    LogicalOp,
    UnaryOp,
)
from aegis.policy.stdlib import STDLIB_FUNCTIONS


def test_literal_and_fieldpath_evaluation():
    ctx = {
        "args": {"amount": 500, "user": {"role": "admin", "tags": ["vip", "staff"]}},
        "agent": {"id": "agent-1"},
    }

    assert Literal(42).evaluate(ctx) == 42
    assert FieldPath("args.amount").evaluate(ctx) == 500
    assert FieldPath("args.user.role").evaluate(ctx) == "admin"
    assert FieldPath("args.user.non_existent").evaluate(ctx) is None


def test_binary_comparisons():
    ctx = {"x": 10, "y": 20, "name": "AegisKernel", "tags": ["sec", "ai"]}

    assert BinaryOp("==", FieldPath("x"), Literal(10)).evaluate(ctx) is True
    assert BinaryOp("<", FieldPath("x"), FieldPath("y")).evaluate(ctx) is True
    assert BinaryOp(">=", FieldPath("x"), Literal(10)).evaluate(ctx) is True
    assert BinaryOp("in", Literal("sec"), FieldPath("tags")).evaluate(ctx) is True
    assert BinaryOp("contains", FieldPath("name"), Literal("Kernel")).evaluate(ctx) is True
    assert BinaryOp("matches", FieldPath("name"), Literal(r"^Aegis")).evaluate(ctx) is True
    assert BinaryOp("+", FieldPath("x"), FieldPath("y")).evaluate(ctx) == 30


def test_logical_and_unary_ops():
    ctx = {"is_active": True, "balance": 100}

    and_node = LogicalOp("AND", [
        BinaryOp("==", FieldPath("is_active"), Literal(True)),
        BinaryOp(">", FieldPath("balance"), Literal(50)),
    ])
    assert and_node.evaluate(ctx) is True

    or_node = LogicalOp("OR", [
        BinaryOp("<", FieldPath("balance"), Literal(10)),
        BinaryOp("==", FieldPath("is_active"), Literal(True)),
    ])
    assert or_node.evaluate(ctx) is True

    not_node = UnaryOp("not", FieldPath("is_active"))
    assert not_node.evaluate(ctx) is False


def test_stdlib_functions():
    assert STDLIB_FUNCTIONS["len"]([1, 2, 3, 4]) == 4
    assert STDLIB_FUNCTIONS["lower"]("AEGIS") == "aegis"
    assert STDLIB_FUNCTIONS["is_valid_email"]("security@agentication.com") is True
    assert STDLIB_FUNCTIONS["is_valid_email"]("not-an-email") is False
    assert STDLIB_FUNCTIONS["is_valid_ip"]("192.168.1.1") is True
    assert STDLIB_FUNCTIONS["ip_in_cidr"]("10.0.1.5", "10.0.0.0/16") is True
    assert STDLIB_FUNCTIONS["ip_in_cidr"]("172.16.0.1", "10.0.0.0/16") is False
    assert STDLIB_FUNCTIONS["has_pii"]("My SSN is 000-12-3456") is True
    assert STDLIB_FUNCTIONS["has_pii"]("My API key is sk-1234567890123456789012") is True
    assert STDLIB_FUNCTIONS["has_pii"]("Regular unclassified message") is False
    assert STDLIB_FUNCTIONS["clamp"](150, 0, 100) == 100
