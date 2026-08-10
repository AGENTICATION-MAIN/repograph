"""
File Metadata and Language Classifier for Repograph.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, Optional

LANGUAGE_MAP: Dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".c": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".rb": "Ruby",
    ".php": "PHP",
    ".sh": "Shell",
    ".bash": "Shell",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".md": "Markdown",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".dockerfile": "Dockerfile",
}

SPECIAL_FILENAMES: Dict[str, str] = {
    "Dockerfile": "Dockerfile",
    "Containerfile": "Dockerfile",
    "Makefile": "Makefile",
    "package.json": "Node Package Manifest",
    "requirements.txt": "Python Requirements Manifest",
    "pyproject.toml": "Python Project Manifest",
    "setup.py": "Python Setup Script",
    "go.mod": "Go Module Manifest",
    "go.sum": "Go Checksums",
    "Cargo.toml": "Rust Cargo Manifest",
    "Cargo.lock": "Rust Cargo Lockfile",
}


def detect_language(path: Path) -> str:
    """Classifies the primary programming language or format of a file."""
    if path.name in SPECIAL_FILENAMES:
        return SPECIAL_FILENAMES[path.name]
    suffix = path.suffix.lower()
    return LANGUAGE_MAP.get(suffix, "Unknown")


def collect_file_metadata(path: Path) -> Dict[str, Any]:
    """Extracts size, line count, language, and SHA-256 hash safely."""
    try:
        stat = path.stat()
        size_bytes = stat.st_size
        language = detect_language(path)

        # Count lines for text files
        line_count = 0
        sha256 = ""
        if size_bytes < 5 * 1024 * 1024:  # Under 5MB
            try:
                with open(path, "rb") as f:
                    content = f.read()
                    sha256 = hashlib.sha256(content).hexdigest()
                    line_count = content.count(b"\n") + (1 if content and not content.endswith(b"\n") else 0)
            except Exception:
                pass

        return {
            "size_bytes": size_bytes,
            "line_count": line_count,
            "language": language,
            "sha256": sha256,
            "is_symlink": path.is_symlink(),
        }
    except Exception as e:
        return {
            "size_bytes": 0,
            "line_count": 0,
            "language": "Unknown",
            "sha256": "",
            "error": str(e),
        }
