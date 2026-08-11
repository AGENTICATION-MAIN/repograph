"""
Safe TOML Deserializer with Python 3.10 compatibility and pure fallback.
"""

from __future__ import annotations

import re
from typing import Any, Dict

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore


def parse_toml_fallback(content: str) -> Dict[str, Any]:
    """
    Lightweight fallback TOML parser for dependencies and package metadata
    when neither tomllib (3.11+) nor tomli (3.10) is installed.
    """
    data: Dict[str, Any] = {}
    current_section = data
    current_section_name = ""

    lines = content.splitlines()
    for line in lines:
        line_str = line.split("#")[0].strip()
        if not line_str:
            continue

        # Match table header [section] or [section.subsection]
        if line_str.startswith("[") and line_str.endswith("]"):
            header = line_str[1:-1].strip()
            parts = header.split(".")
            curr = data
            for part in parts:
                if part not in curr or not isinstance(curr[part], dict):
                    curr[part] = {}
                curr = curr[part]
            current_section = curr
            current_section_name = header
            continue

        # Match key = value or key = "val"
        if "=" in line_str:
            k, _, v = line_str.partition("=")
            key = k.strip().strip('"').strip("'")
            val_str = v.strip()

            # String
            if (val_str.startswith('"') and val_str.endswith('"')) or (val_str.startswith("'") and val_str.endswith("'")):
                current_section[key] = val_str[1:-1]
            # List: e.g. ["a", "b"]
            elif val_str.startswith("[") and val_str.endswith("]"):
                items = re.findall(r"['\"]([^'\"]+)['\"]", val_str)
                current_section[key] = items
            # Inline dict: { version = "1.0", features = ["full"] }
            elif val_str.startswith("{") and val_str.endswith("}"):
                sub_dict = {}
                m_ver = re.search(r'version\s*=\s*["\']([^"\']+)["\']', val_str)
                if m_ver:
                    sub_dict["version"] = m_ver.group(1)
                current_section[key] = sub_dict
            else:
                current_section[key] = val_str

    return data


def safe_load_toml(content: str) -> Dict[str, Any]:
    """Loads TOML content using standard tomllib/tomli or fallback."""
    if tomllib is not None:
        try:
            return tomllib.loads(content)
        except Exception:
            return parse_toml_fallback(content)
    return parse_toml_fallback(content)
