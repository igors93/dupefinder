"""Filtering rules for files and directories."""

from __future__ import annotations

from pathlib import Path

from dupefinder.models import ScanOptions
from dupefinder.safety import is_hidden_path, normalize_extension


def should_ignore_directory(path: Path, options: ScanOptions, *, is_root: bool = False) -> bool:
    """Return True when a directory should not be scanned."""

    if is_root:
        return False
    if path.name in options.ignored_dirs:
        return True
    if options.ignore_hidden and is_hidden_path(path):
        return True
    if path.is_symlink() and not options.follow_symlinks:
        return True
    return False


def should_ignore_file(path: Path, size: int, options: ScanOptions) -> bool:
    """Return True when a file should be skipped."""

    if size < options.min_size:
        return True
    if options.max_size is not None and size > options.max_size:
        return True
    if options.ignore_hidden and is_hidden_path(path):
        return True
    if path.is_symlink() and not options.follow_symlinks:
        return True

    extension = normalize_extension(path.suffix)
    if options.include_extensions is not None and extension not in options.include_extensions:
        return True
    if extension in options.ignored_extensions:
        return True
    return False
