"""Hashing utilities.

Files are read in chunks to avoid loading large files into memory.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, Iterator, List

from dupefinder.errors import FileHashError, UnsupportedHashAlgorithmError
from dupefinder.models import FileInfo, ScanIssue, ScanOptions


def hash_file(path: str | Path, *, algorithm: str = "sha256", chunk_size: int = 1024 * 1024) -> str:
    """Return the hexadecimal hash digest for a file.

    Parameters
    ----------
    path:
        File to hash.
    algorithm:
        Any algorithm supported by hashlib on the current Python installation.
    chunk_size:
        Number of bytes to read at a time.
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
                hasher.update(chunk)
    except OSError as exc:
        raise FileHashError(f"Cannot hash file {file_path}: {exc}") from exc

    return hasher.hexdigest()


def hash_files(
    files: Iterable[FileInfo],
    options: ScanOptions,
    issues: List[ScanIssue] | None = None,
) -> Iterator[FileInfo]:
    """Yield FileInfo objects with the digest field filled."""

    for file_info in files:
        try:
            digest = hash_file(
                file_info.path,
                algorithm=options.algorithm,
                chunk_size=options.chunk_size,
            )
        except FileHashError as exc:
            if options.on_error == "raise":
                raise
            if issues is not None:
                issues.append(ScanIssue(path=file_info.path, message=str(exc), phase="hash"))
            continue
        yield FileInfo(path=file_info.path, size=file_info.size, digest=digest)
