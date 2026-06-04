"""Scan event system."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dupefinder.models import DuplicateGroup, ScanIssue


@dataclass(frozen=True)
class ScanEvent:
    """An event emitted during a scan. Not all fields are relevant for every event type."""

    type: str  # scan_started, file_discovered, file_hashed, duplicate_group_found, issue, scan_completed, scan_cancelled
    root: Path | None = None
    path: Path | None = None
    scanned_files: int = 0
    hashed_files: int = 0
    total_candidates: int = 0
    duplicate_groups: int = 0
    elapsed_seconds: float | None = None
    message: str | None = None
    issue: ScanIssue | None = None
    group: DuplicateGroup | None = None
    from_cache: bool = False
    bytes_read: int = 0


@dataclass(frozen=True)
class ScanProgress:
    """A simplified progress snapshot emitted during a scan.

    Delivered to the ``on_progress`` callback of ``DupeFinder``.
    Unlike ``ScanEvent``, this model always has a complete and meaningful
    set of counters regardless of the current phase.
    """

    root: Path
    phase: str  # "discovery", "hashing", "grouping", "done"
    scanned_files: int = 0
    hashed_files: int = 0
    total_candidates: int = 0
    duplicate_groups: int = 0
    elapsed_seconds: float | None = None
    cancelled: bool = False
