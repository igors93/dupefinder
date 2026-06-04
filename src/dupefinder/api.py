"""Public API for dupefinder.

Keep this module small and friendly. It is the main doorway for people using
the library in their own projects.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from dupefinder.grouping import build_duplicate_groups
from dupefinder.models import DuplicateGroup, ScanIssue, ScanOptions, ScanReport
from dupefinder.safety import validate_options, validate_scan_path
from dupefinder.scanner import iter_files


def scan(path: str | Path, options: ScanOptions | None = None) -> ScanReport:
    """Scan a path and return a complete report.

    This function never deletes, moves, or modifies files.
    """

    selected_options = options or ScanOptions()
    validate_options(selected_options)
    root = validate_scan_path(path)

    issues: list[ScanIssue] = []
    files = list(iter_files(root, selected_options, issues))
    groups, hashed_files = build_duplicate_groups(files, selected_options, issues)

    return ScanReport(
        root=root,
        groups=groups,
        scanned_files=len(files),
        hashed_files=hashed_files,
        issues=tuple(issues),
    )


def find_duplicates(path: str | Path, options: ScanOptions | None = None) -> Tuple[DuplicateGroup, ...]:
    """Return only the duplicate groups for simple use cases."""

    return scan(path, options=options).groups
