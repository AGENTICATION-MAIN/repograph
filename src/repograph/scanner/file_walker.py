"""
Safe Repository File Walker for Repograph.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple

from repograph.core.config import RepographConfig
from repograph.core.exceptions import ScanError, UnsafePathError
from repograph.scanner.ignore_rules import IgnoreMatcher
from repograph.scanner.metadata_collector import collect_file_metadata


class FileWalker:
    """
    Safe directory tree walker.
    Enforces maximum depth, respects ignore rules, prevents symlink cycles,
    and isolates untrusted repositories.
    """

    def __init__(self, root_path: Path, config: Optional[RepographConfig] = None):
        self.root_path = root_path.resolve()
        if not self.root_path.exists():
            raise ScanError(f"Target repository path does not exist: {self.root_path}")
        if not self.root_path.is_dir():
            raise ScanError(f"Target repository path is not a directory: {self.root_path}")

        self.config = config or RepographConfig()
        self.ignore_matcher = IgnoreMatcher(
            root_dir=self.root_path,
            custom_patterns=self.config.custom_ignore_patterns,
        )

    def walk(self) -> Generator[Tuple[Path, str, Dict[str, Any]], None, None]:
        """
        Traverses repository files yielding (absolute_path, relative_posix_path, metadata_dict).
        """
        visited_dirs = set()

        for dirpath_str, dirnames, filenames in os.walk(self.root_path, followlinks=self.config.follow_symlinks):
            current_dir = Path(dirpath_str).resolve()

            # Prevent circular symlink loops
            if current_dir in visited_dirs:
                dirnames.clear()
                continue
            visited_dirs.add(current_dir)

            # Compute relative depth
            try:
                rel_dir = current_dir.relative_to(self.root_path)
            except ValueError:
                # Outside root boundary
                dirnames.clear()
                continue

            depth = len(rel_dir.parts)
            if depth > self.config.max_depth:
                dirnames.clear()
                continue

            # Filter directories in-place
            filtered_dirnames = []
            for d in dirnames:
                rel_sub = (rel_dir / d).as_posix() if rel_dir.parts else d
                if not self.ignore_matcher.should_ignore_dir(d, rel_sub):
                    filtered_dirnames.append(d)
            dirnames[:] = filtered_dirnames

            # Process files
            for fname in filenames:
                rel_file = (rel_dir / fname).as_posix() if rel_dir.parts else fname
                if self.ignore_matcher.should_ignore_file(fname, rel_file):
                    continue

                abs_file = current_dir / fname
                meta = collect_file_metadata(abs_file)
                yield abs_file, rel_file, meta
