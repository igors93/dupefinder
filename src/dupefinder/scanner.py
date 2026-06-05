"""File discovery logic."""
from __future__ import annotations

import os
from collections.abc import Collection, Iterator
from pathlib import Path

from dupefinder.errors import FileAccessError
from dupefinder.filters import should_ignore_directory, should_ignore_file
from dupefinder.models import FileInfo, ScanIssue, ScanOptions


def iter_files(
    root: Path,
    options: ScanOptions,
    issues: list[ScanIssue] | None = None,
    *,
    excluded_paths: Collection[Path] = (),
) -> Iterator[FileInfo]:
    """Yield files that pass filters and are not owned by internal helpers."""
    excluded = frozenset(path.expanduser().absolute() for path in excluded_paths)
    if root.is_file():
        yield from _iter_single_file(root, options, issues, excluded)
        return
    yield from _walk_directory(root, options, issues, excluded)


def _iter_single_file(
    path: Path,
    options: ScanOptions,
    issues: list[ScanIssue] | None,
    excluded_paths: frozenset[Path],
) -> Iterator[FileInfo]:
    if _is_excluded(path, excluded_paths):
        return
    try:
        stat = path.stat() if options.follow_symlinks else path.lstat()
    except OSError as exc:
        _handle_scan_error(path, exc, options, issues)
        return
    if not should_ignore_file(path, stat.st_size, options):
        yield FileInfo(path=path, size=stat.st_size)


def _walk_directory(
    root: Path,
    options: ScanOptions,
    issues: list[ScanIssue] | None,
    excluded_paths: frozenset[Path],
) -> Iterator[FileInfo]:
    stack: list[tuple[Path, int]] = [(root, 0)]
    visited_dirs: set[tuple[int, int]] = set()

    while stack:
        current, depth = stack.pop()
        try:
            stat = current.stat() if options.follow_symlinks else current.lstat()
        except OSError as exc:
            _handle_scan_error(current, exc, options, issues)
            continue

        directory_id = (getattr(stat, "st_dev", 0), getattr(stat, "st_ino", 0))
        if directory_id in visited_dirs:
            continue
        visited_dirs.add(directory_id)

        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    if _is_excluded(path, excluded_paths):
                        continue
                    try:
                        if entry.is_dir(follow_symlinks=options.follow_symlinks):
                            if options.max_depth is not None and depth >= options.max_depth:
                                continue
                            if not should_ignore_directory(path, options):
                                stack.append((path, depth + 1))
                            continue
                        if not entry.is_file(follow_symlinks=options.follow_symlinks):
                            continue
                        file_stat = entry.stat(follow_symlinks=options.follow_symlinks)
                    except OSError as exc:
                        _handle_scan_error(path, exc, options, issues)
                        continue
                    if should_ignore_file(path, file_stat.st_size, options):
                        continue
                    yield FileInfo(path=path, size=file_stat.st_size)
        except OSError as exc:
            _handle_scan_error(current, exc, options, issues)


def _is_excluded(path: Path, excluded_paths: frozenset[Path]) -> bool:
    return path.expanduser().absolute() in excluded_paths


def _handle_scan_error(
    path: Path,
    exc: OSError,
    options: ScanOptions,
    issues: list[ScanIssue] | None,
) -> None:
    message = f"Cannot access path: {exc}"
    if options.on_error == "raise":
        raise FileAccessError(message) from exc
    if issues is not None:
        issues.append(ScanIssue(path=path, message=message, phase="scan"))
