"""File discovery logic.

The scanner only finds candidate files. It does not hash them and it does not
decide which files are duplicates. This separation keeps maintenance simple.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator, List

from dupefinder.errors import FileAccessError
from dupefinder.filters import should_ignore_directory, should_ignore_file
from dupefinder.models import FileInfo, ScanIssue, ScanOptions


def iter_files(root: Path, options: ScanOptions, issues: List[ScanIssue] | None = None) -> Iterator[FileInfo]:
    """Yield files that pass the configured filters.

    Errors are either recorded as ScanIssue objects or raised, depending on
    options.on_error.
    """

    if root.is_file():
        yield from _iter_single_file(root, options, issues)
        return

    yield from _walk_directory(root, options, issues)


def _iter_single_file(path: Path, options: ScanOptions, issues: List[ScanIssue] | None) -> Iterator[FileInfo]:
    try:
        stat = path.stat() if options.follow_symlinks else path.lstat()
    except OSError as exc:
        _handle_scan_error(path, exc, options, issues)
        return

    if not should_ignore_file(path, stat.st_size, options):
        yield FileInfo(path=path, size=stat.st_size)


def _walk_directory(root: Path, options: ScanOptions, issues: List[ScanIssue] | None) -> Iterator[FileInfo]:
    stack = [root]
    visited_dirs: set[tuple[int, int]] = set()

    while stack:
        current = stack.pop()

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
                    try:
                        if entry.is_dir(follow_symlinks=options.follow_symlinks):
                            if not should_ignore_directory(path, options):
                                stack.append(path)
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


def _handle_scan_error(
    path: Path,
    exc: OSError,
    options: ScanOptions,
    issues: List[ScanIssue] | None,
) -> None:
    message = f"Cannot access path: {exc}"
    if options.on_error == "raise":
        raise FileAccessError(message) from exc
    if issues is not None:
        issues.append(ScanIssue(path=path, message=message, phase="scan"))
