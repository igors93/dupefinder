"""Validation helpers and safe defaults."""

from __future__ import annotations

import hashlib
from pathlib import Path

from dupefinder.errors import InvalidOptionError, InvalidPathError, UnsupportedHashAlgorithmError
from dupefinder.models import ScanOptions


def normalize_path(path: str | Path) -> Path:
    """Return an absolute Path without requiring the target to exist."""

    return Path(path).expanduser().resolve(strict=False)


def validate_scan_path(path: str | Path) -> Path:
    """Validate and normalize a path before scanning."""

    normalized = normalize_path(path)
    if not normalized.exists():
        raise InvalidPathError(f"Path does not exist: {normalized}")
    if not (normalized.is_dir() or normalized.is_file()):
        raise InvalidPathError(f"Path is not a regular file or directory: {normalized}")
    return normalized


def validate_options(options: ScanOptions) -> None:
    """Validate options early so errors are clear."""

    if options.algorithm not in hashlib.algorithms_available:
        raise UnsupportedHashAlgorithmError(
            f"Unsupported hash algorithm: {options.algorithm!r}. "
            "Use an algorithm available in hashlib.algorithms_available."
        )
    if options.chunk_size <= 0:
        raise InvalidOptionError("chunk_size must be greater than zero.")
    if options.min_size < 0:
        raise InvalidOptionError("min_size cannot be negative.")
    if options.max_size is not None and options.max_size < options.min_size:
        raise InvalidOptionError("max_size cannot be smaller than min_size.")
    if options.on_error not in {"skip", "raise"}:
        raise InvalidOptionError('on_error must be "skip" or "raise".')


def is_hidden_path(path: Path) -> bool:
    """Return True when any visible path part starts with a dot.

    This is a portable rule. Native Windows hidden attributes are not inspected,
    keeping the project dependency-free and simple.
    """

    return any(part.startswith(".") and part not in {".", ".."} for part in path.parts)


def normalize_extension(extension: str) -> str:
    """Normalize extensions to a lowercase '.ext' format."""

    cleaned = extension.strip().lower()
    if not cleaned:
        return cleaned
    return cleaned if cleaned.startswith(".") else f".{cleaned}"


def normalize_extensions(extensions: frozenset[str] | set[str] | tuple[str, ...] | list[str]) -> frozenset[str]:
    """Normalize a collection of extensions."""

    return frozenset(ext for ext in (normalize_extension(item) for item in extensions) if ext)
