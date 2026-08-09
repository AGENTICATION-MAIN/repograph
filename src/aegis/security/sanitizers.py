"""
Deterministic Data Sanitizers for AegisKernel.
"""

from __future__ import annotations

import html
import re
from typing import Any, Dict, List, Optional


def sanitize_html(text: str) -> str:
    """Escapes HTML entities and strips potentially dangerous script tags."""
    if not isinstance(text, str):
        return text
    # Strip script and iframe tags
    no_scripts = re.sub(r"<(script|iframe|style)[^>]*>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return html.escape(no_scripts)


def mask_pii(text: str) -> str:
    """Masks SSNs, credit card numbers, and API tokens with redacted placeholders."""
    if not isinstance(text, str):
        return text
    # Mask SSN
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]", text)
    # Mask credit cards
    text = re.sub(r"\b(?:\d[ -]*?){13,16}\b", "[REDACTED_CREDIT_CARD]", text)
    # Mask API tokens
    text = re.sub(r"\b(sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{20,})\b", "[REDACTED_SECRET_KEY]", text)
    return text


def sanitize_sql_identifier(identifier: str) -> str:
    """Ensures SQL identifiers (tables, columns) contain only alphanumeric and underscore characters."""
    if not isinstance(identifier, str):
        raise ValueError("SQL identifier must be a string")
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "", identifier)
    if not cleaned or not cleaned[0].isalpha():
        raise ValueError(f"Invalid SQL identifier: '{identifier}'")
    return cleaned


def sanitize_shell_arg(arg: str) -> str:
    """Escapes shell argument to prevent injection."""
    if not isinstance(arg, str):
        arg = str(arg)
    # Wrap in single quotes and replace single quotes with '\''
    escaped = "'" + arg.replace("'", "'\\''") + "'"
    return escaped


class SanitizerRegistry:
    """Registry of standard sanitizers for degrading or safe-wrapping tainted data."""

    @staticmethod
    def apply_sanitizer(sanitizer_name: str, value: Any) -> Any:
        if sanitizer_name == "html_escape_sanitizer":
            return sanitize_html(str(value))
        elif sanitizer_name == "pii_masker":
            return mask_pii(str(value))
        elif sanitizer_name == "sql_identifier_sanitizer":
            return sanitize_sql_identifier(str(value))
        elif sanitizer_name == "shell_escape_sanitizer":
            return sanitize_shell_arg(str(value))
        return value
