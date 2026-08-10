"""
Ignore Rules and Pattern Matching for Repograph.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import List, Set

DEFAULT_IGNORE_DIRS: Set[str] = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    "target",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".output",
    "coverage",
    ".coverage",
    "vendor",
    ".cache",
    ".idea",
    ".vscode",
}

DEFAULT_IGNORE_EXTENSIONS: Set[str] = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib", ".exe", ".bin",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".pdf", ".docx", ".xlsx", ".pptx",
    ".ttf", ".woff", ".woff2", ".eot",
    ".class", ".jar", ".war",
}


class IgnoreMatcher:
    """Matches files and directories against standard ignore patterns and .gitignore files."""

    def __init__(self, root_dir: Path, custom_patterns: List[str] = None):
        self.root_dir = root_dir.resolve()
        self.patterns: List[str] = list(custom_patterns or [])
        self._load_gitignore()

    def _load_gitignore(self) -> None:
        gitignore_path = self.root_dir / ".gitignore"
        if gitignore_path.is_file():
            try:
                with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            self.patterns.append(line)
            except Exception:
                pass

    def should_ignore_dir(self, dir_name: str, relative_path: str) -> bool:
        if dir_name in DEFAULT_IGNORE_DIRS:
            return True
        for pattern in self.patterns:
            pat = pattern.rstrip("/")
            if fnmatch.fnmatch(dir_name, pat) or fnmatch.fnmatch(relative_path, pat):
                return True
        return False

    def should_ignore_file(self, file_name: str, relative_path: str) -> bool:
        path = Path(file_name)
        if path.suffix.lower() in DEFAULT_IGNORE_EXTENSIONS:
            return True
        for pattern in self.patterns:
            if fnmatch.fnmatch(file_name, pattern) or fnmatch.fnmatch(relative_path, pattern):
                return True
        return False
