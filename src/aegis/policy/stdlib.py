"""
Standard Library of Deterministic Functions for Aegis Policy DSL.

Provides safe, pure mathematical, string, set, regex, and security evaluation helpers.
"""

from __future__ import annotations

import ipaddress
import re
from typing import Any, Callable, Dict, List, Optional, Union


def fn_len(val: Any) -> int:
    """Returns the length of a collection or string, or 0 if None."""
    if val is None:
        return 0
    if hasattr(val, "__len__"):
        return len(val)
    return 0


def fn_lower(val: Any) -> str:
    """Converts string to lowercase."""
    return str(val).lower() if val is not None else ""


def fn_upper(val: Any) -> str:
    """Converts string to uppercase."""
    return str(val).upper() if val is not None else ""


def fn_is_valid_email(val: Any) -> bool:
    """Validates if string matches RFC-compliant email structure."""
    if not val or not isinstance(val, str):
        return False
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, val))


def fn_is_valid_ip(val: Any) -> bool:
    """Validates if string is a valid IPv4 or IPv6 address."""
    if not val or not isinstance(val, str):
        return False
    try:
        ipaddress.ip_address(val.strip())
        return True
    except ValueError:
        return False


def fn_ip_in_cidr(ip_str: Any, cidr_str: Any) -> bool:
    """Checks if an IP address is within a specified CIDR range."""
    if not ip_str or not cidr_str:
        return False
    try:
        ip = ipaddress.ip_address(str(ip_str).strip())
        net = ipaddress.ip_network(str(cidr_str).strip(), strict=False)
        return ip in net
    except ValueError:
        return False


def fn_contains_any(container: Any, candidates: Any) -> bool:
    """Checks if container contains any of candidate items."""
    if container is None or candidates is None:
        return False
    if isinstance(candidates, (str, int, float)):
        candidates = [candidates]
    for c in candidates:
        if isinstance(container, str) and str(c) in container:
            return True
        if isinstance(container, (list, tuple, set)) and c in container:
            return True
    return False


def fn_contains_all(container: Any, candidates: Any) -> bool:
    """Checks if container contains all candidate items."""
    if container is None or candidates is None:
        return False
    if isinstance(candidates, (str, int, float)):
        candidates = [candidates]
    for c in candidates:
        if isinstance(container, str) and str(c) not in container:
            return False
        if isinstance(container, (list, tuple, set)) and c not in container:
            return False
    return True


def fn_has_pii(text: Any) -> bool:
    """
    Deterministic regex-based scanner for sensitive PII (SSNs, credit cards, secret keys).
    """
    if not text or not isinstance(text, str):
        return False
    # SSN pattern: 000-00-0000
    if re.search(r"\b\d{3}-\d{2}-\d{4}\b", text):
        return True
    # Standard credit card numbers (Visa, MC, Amex, Discover)
    if re.search(r"\b(?:\d[ -]*?){13,16}\b", text):
        # Run Luhn check on potential card digits
        digits = re.sub(r"\D", "", text)
        if len(digits) in (15, 16):
            sum_ = 0
            rev = digits[::-1]
            for i, d in enumerate(rev):
                n = int(d)
                if i % 2 == 1:
                    n *= 2
                    if n > 9:
                        n -= 9
                sum_ += n
            if sum_ % 10 == 0:
                return True
    # API key patterns (Bearer tokens, AWS keys AKIA..., sk-..., ghp_...)
    if re.search(r"\b(sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{20,})\b", text):
        return True
    return False


def fn_clamp(val: Any, min_val: Any, max_val: Any) -> Any:
    """Clamps a numeric value within [min_val, max_val]."""
    if val is None:
        return min_val
    return max(min_val, min(val, max_val))


def fn_abs(val: Any) -> Any:
    """Returns absolute value."""
    return abs(val) if val is not None else 0


STDLIB_FUNCTIONS: Dict[str, Callable[..., Any]] = {
    "len": fn_len,
    "lower": fn_lower,
    "upper": fn_upper,
    "is_valid_email": fn_is_valid_email,
    "is_valid_ip": fn_is_valid_ip,
    "ip_in_cidr": fn_ip_in_cidr,
    "contains_any": fn_contains_any,
    "contains_all": fn_contains_all,
    "has_pii": fn_has_pii,
    "clamp": fn_clamp,
    "abs": fn_abs,
}
