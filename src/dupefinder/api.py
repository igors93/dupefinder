"""Public API for dupefinder."""
from __future__ import annotations

from pathlib import Path

from dupefinder.engine import DupeFinder
from dupefinder.models import DuplicateGroup, ScanOptions, ScanReport


def scan(path: str | Path, options: ScanOptions | None = None) -> ScanReport:
    """Scan a path and return a complete report.

    This function never deletes, moves, or modifies files.
    """
    return DupeFinder(options=options).scan(path)


def find_duplicates(path: str | Path, options: ScanOptions | None = None) -> tuple[DuplicateGroup, ...]:
    """Return only the duplicate groups for simple use cases."""
    return scan(path, options=options).groups
