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
