"""Data models used by dupefinder.

These classes are intentionally small and explicit. They make the public API
predictable and avoid returning loose dictionaries with unclear keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from dupefinder.constants import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_HASH_ALGORITHM,
    DEFAULT_IGNORED_DIRS,
    DEFAULT_MIN_SIZE,
)


@dataclass(frozen=True)
class ScanOptions:
    """Options used to control a duplicate scan.

    Defaults are conservative: the scan is read-only, hidden paths are ignored,
    and symbolic links are not followed.
    """

    algorithm: str = DEFAULT_HASH_ALGORITHM
    chunk_size: int = DEFAULT_CHUNK_SIZE
    min_size: int = DEFAULT_MIN_SIZE
    max_size: int | None = None
    ignore_hidden: bool = True
    follow_symlinks: bool = False
    ignored_dirs: frozenset[str] = field(default_factory=lambda: DEFAULT_IGNORED_DIRS)
    ignored_extensions: frozenset[str] = field(default_factory=frozenset)
    include_extensions: Optional[frozenset[str]] = None
    on_error: Literal["skip", "raise"] = "skip"


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


@dataclass(frozen=True)
class ScanIssue:
    """Non-fatal problem found during a scan."""

    path: Path
    message: str
    phase: str


@dataclass(frozen=True)
class ScanReport:
    """Complete result of a duplicate scan."""

    root: Path
    groups: tuple[DuplicateGroup, ...]
    scanned_files: int
    hashed_files: int
    issues: tuple[ScanIssue, ...] = field(default_factory=tuple)

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
