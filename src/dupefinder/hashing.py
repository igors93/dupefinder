"""Hashing utilities.

Files are read in chunks to avoid loading large files into memory.
"""

from __future__ import annotations

import hashlib
import sqlite3
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path

from dupefinder.errors import FileHashError, UnsupportedHashAlgorithmError
from dupefinder.models import FileInfo, ScanIssue, ScanOptions


def hash_file(
    path: str | Path,
    *,
    algorithm: str = "sha256",
    chunk_size: int = 1024 * 1024,
    should_cancel: Callable[[], bool] | None = None,
    on_bytes_read: Callable[[int], None] | None = None,
) -> str:
    """Return the hexadecimal hash digest for a file.

    Parameters
    ----------
    path:
        File to hash.
    algorithm:
        Any algorithm supported by hashlib on the current Python installation.
    chunk_size:
        Number of bytes to read at a time.
    should_cancel:
        Optional callable; if it returns True between chunks, raises _ScanCancelled.
    on_bytes_read:
        Optional callable invoked with the number of bytes read after each chunk.
    """

    if algorithm not in hashlib.algorithms_available:
        raise UnsupportedHashAlgorithmError(f"Unsupported hash algorithm: {algorithm!r}")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    hasher = hashlib.new(algorithm)
    file_path = Path(path)

    try:
        with file_path.open("rb") as file_obj:
            while True:
                chunk = file_obj.read(chunk_size)
                if not chunk:
                    break
                # Check cancellation after reading the chunk but before digesting
                if should_cancel is not None and should_cancel():
                    from dupefinder.errors import _ScanCancelled

                    raise _ScanCancelled()
                hasher.update(chunk)
                if on_bytes_read is not None:
                    on_bytes_read(len(chunk))
    except OSError as exc:
        raise FileHashError(f"Cannot hash file {file_path}: {exc}") from exc

    return hasher.hexdigest()


def _resolve_digest(
    file_info: FileInfo,
    options: ScanOptions,
    cache: object | None,
    *,
    should_cancel: Callable[[], bool] | None = None,
    on_bytes_read: Callable[[int], None] | None = None,
) -> str:
    """Return the digest for a file, using the cache when available."""
    mtime_ns: int | None = None

    if cache is not None:
        try:
            mtime_ns = file_info.path.stat().st_mtime_ns
            cached = cache.get(  # type: ignore[union-attr]
                file_info.path,
                size=file_info.size,
                mtime_ns=mtime_ns,
                algorithm=options.algorithm,
            )
            if cached is not None:
                return cached
        except (OSError, sqlite3.Error):
            pass

    digest = hash_file(
        file_info.path,
        algorithm=options.algorithm,
        chunk_size=options.chunk_size,
        should_cancel=should_cancel,
        on_bytes_read=on_bytes_read,
    )

    if cache is not None and mtime_ns is not None:
        try:
            cache.set(  # type: ignore[union-attr]
                file_info.path,
                size=file_info.size,
                mtime_ns=mtime_ns,
                algorithm=options.algorithm,
                digest=digest,
            )
        except (OSError, sqlite3.Error):
            pass

    return digest


def hash_files(
    files: Iterable[FileInfo],
    options: ScanOptions,
    issues: list[ScanIssue] | None = None,
    *,
    cache: object | None = None,
    should_cancel: Callable[[], bool] | None = None,
    on_bytes_read: Callable[[int], None] | None = None,
) -> Iterator[FileInfo]:
    """Yield FileInfo objects with the digest field filled.

    _ScanCancelled is NOT caught here — it propagates to the engine.
    """

    for file_info in files:
        try:
            digest = _resolve_digest(
                file_info,
                options,
                cache,
                should_cancel=should_cancel,
                on_bytes_read=on_bytes_read,
            )
        except FileHashError as exc:
            if options.on_error == "raise":
                raise
            if issues is not None:
                issues.append(ScanIssue(path=file_info.path, message=str(exc), phase="hash"))
            continue
        # _ScanCancelled is NOT caught here — it propagates to the engine
        yield FileInfo(path=file_info.path, size=file_info.size, digest=digest)
