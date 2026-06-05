"""Data models used by dupefinder."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from dupefinder.constants import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_HASH_ALGORITHM,
    DEFAULT_IGNORED_DIRS,
    DEFAULT_MIN_SIZE,
)


@dataclass(frozen=True)
class ScanOptions:
    """Options used to control a duplicate scan."""

    algorithm: str = DEFAULT_HASH_ALGORITHM
    chunk_size: int = DEFAULT_CHUNK_SIZE
    min_size: int = DEFAULT_MIN_SIZE
    max_size: int | None = None
    ignore_hidden: bool = True
    follow_symlinks: bool = False
    ignored_dirs: frozenset[str] = field(default_factory=lambda: DEFAULT_IGNORED_DIRS)
    ignored_extensions: frozenset[str] = field(default_factory=frozenset)
    include_extensions: frozenset[str] | None = None
    on_error: Literal["skip", "raise"] = "skip"
    max_files: int | None = None
    max_depth: int | None = None
    timeout_seconds: float | None = None


@dataclass(frozen=True)
class FileInfo:
    """Information about a scanned file."""

    path: Path
    size: int
    digest: str | None = None


@dataclass(frozen=True)
class DuplicateGroup:
    """A group of files that have the same size and hash."""

    digest: str
    size: int
    files: tuple[Path, ...]

    @property
    def count(self) -> int:
        return len(self.files)

    @property
    def wasted_space(self) -> int:
        """Bytes that could be saved if only one file from this group remained."""
        if self.count <= 1:
            return 0
        return self.size * (self.count - 1)

    def to_dict(self) -> dict[str, Any]:
        from dupefinder.report import group_to_dict
        return group_to_dict(self)


@dataclass(frozen=True)
class ScanIssue:
    """Non-fatal problem found during a scan."""

    path: Path
    message: str
    phase: str

    def to_dict(self) -> dict[str, Any]:
        from dupefinder.report import issue_to_dict
        return issue_to_dict(self)


@dataclass(frozen=True)
class ScanReport:
    """Complete result of a duplicate scan."""

    root: Path
    groups: tuple[DuplicateGroup, ...]
    scanned_files: int
    hashed_files: int
    issues: tuple[ScanIssue, ...] = field(default_factory=tuple)
    cancelled: bool = False
    elapsed_seconds: float | None = None
    total_bytes_read: int | None = None

    @property
    def total_groups(self) -> int:
        return len(self.groups)

    @property
    def total_duplicate_files(self) -> int:
        return sum(group.count for group in self.groups)

    @property
    def total_wasted_space(self) -> int:
        return sum(group.wasted_space for group in self.groups)

    @property
    def has_duplicates(self) -> bool:
        return bool(self.groups)

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    def to_dict(self) -> dict[str, Any]:
        from dupefinder.report import report_to_dict
        return report_to_dict(self)

    def to_json(self, *, indent: int | None = 2) -> str:
        from dupefinder.report import report_to_json
        return report_to_json(self, indent=indent)
