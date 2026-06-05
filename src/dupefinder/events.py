"""Scan event system."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dupefinder.models import DuplicateGroup, ScanIssue

EventType = Literal[
    "scan_started",
    "file_discovered",
    "file_hashed",
    "duplicate_group_found",
    "issue",
    "scan_completed",
    "scan_cancelled",
]
ProgressPhase = Literal["discovery", "hashing", "done"]


@dataclass(frozen=True)
class ScanEvent:
    """An event emitted during a scan."""

    type: EventType
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
    """A simplified progress snapshot emitted during a scan."""

    root: Path
    phase: ProgressPhase
    scanned_files: int = 0
    hashed_files: int = 0
    total_candidates: int = 0
    duplicate_groups: int = 0
    elapsed_seconds: float | None = None
    cancelled: bool = False
