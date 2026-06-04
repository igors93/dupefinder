"""Duplicate grouping logic."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

from dupefinder.hashing import hash_files
from dupefinder.models import DuplicateGroup, FileInfo, ScanIssue, ScanOptions


def group_by_size(files: Iterable[FileInfo]) -> dict[int, list[FileInfo]]:
    """Group files by size.

    Files with different sizes cannot be byte-for-byte duplicates, so this is a
    cheap first pass before calculating hashes.
    """

    grouped: dict[int, list[FileInfo]] = defaultdict(list)
    for file_info in files:
        grouped[file_info.size].append(file_info)
    return dict(grouped)


def candidate_files(by_size: dict[int, list[FileInfo]]) -> list[FileInfo]:
    """Return files that share a size with at least one other file."""
    return [f for same_size in by_size.values() if len(same_size) > 1 for f in same_size]


def groups_from_hash_map(
    by_hash: dict[tuple[int, str], list[Path]],
) -> list[DuplicateGroup]:
    """Build and sort duplicate groups from a (size, digest) -> paths mapping."""
    groups = []
    for (size, digest), paths in by_hash.items():
        if len(paths) > 1:
            groups.append(DuplicateGroup(digest=digest, size=size, files=tuple(sorted(paths))))
    groups.sort(key=lambda g: (g.size, g.digest, tuple(str(p) for p in g.files)))
    return groups


def build_duplicate_groups(
    files: Iterable[FileInfo],
    options: ScanOptions,
    issues: list[ScanIssue] | None = None,
    *,
    cache: object | None = None,
) -> tuple[tuple[DuplicateGroup, ...], int]:
    """Return duplicate groups and the number of files that were hashed."""

    by_size = group_by_size(files)
    candidates = candidate_files(by_size)

    hashed_count = 0
    by_hash: dict[tuple[int, str], list[Path]] = defaultdict(list)

    for file_info in hash_files(candidates, options, issues, cache=cache):
        if file_info.digest is None:
            continue
        hashed_count += 1
        by_hash[(file_info.size, file_info.digest)].append(file_info.path)

    return tuple(groups_from_hash_map(by_hash)), hashed_count
