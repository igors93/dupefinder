"""Optional hash cache using SQLite from the standard library."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class HashCache(Protocol):
    """Interface for hash caches."""

    def get(self, path: Path, *, size: int, mtime_ns: int, algorithm: str) -> str | None: ...
    def set(
        self,
        path: Path,
        *,
        size: int,
        mtime_ns: int,
        algorithm: str,
        digest: str,
    ) -> None: ...
    def close(self) -> None: ...


class SQLiteHashCache:
    """Hash cache backed by a SQLite database."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path).expanduser().absolute()
        self._conn: sqlite3.Connection = sqlite3.connect(self._db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS hash_cache (
                path      TEXT    NOT NULL,
                algorithm TEXT    NOT NULL,
                size      INTEGER NOT NULL,
                mtime_ns  INTEGER NOT NULL,
                digest    TEXT    NOT NULL,
                PRIMARY KEY (path, algorithm)
            )
            """
        )
        self._conn.commit()

    @property
    def excluded_paths(self) -> frozenset[Path]:
        """Files owned by SQLite that must not be included in a scan."""
        base = self._db_path
        return frozenset(
            {
                base,
                Path(f"{base}-wal"),
                Path(f"{base}-shm"),
                Path(f"{base}-journal"),
            }
        )

    def get(self, path: Path, *, size: int, mtime_ns: int, algorithm: str) -> str | None:
        row = self._conn.execute(
            "SELECT digest, size, mtime_ns FROM hash_cache WHERE path = ? AND algorithm = ?",
            (str(path), algorithm),
        ).fetchone()
        if row is None:
            return None
        cached_digest, cached_size, cached_mtime_ns = row
        if cached_size != size or cached_mtime_ns != mtime_ns:
            return None
        return str(cached_digest)

    def set(
        self,
        path: Path,
        *,
        size: int,
        mtime_ns: int,
        algorithm: str,
        digest: str,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO hash_cache (path, algorithm, size, mtime_ns, digest)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (path, algorithm) DO UPDATE SET
                size     = excluded.size,
                mtime_ns = excluded.mtime_ns,
                digest   = excluded.digest
            """,
            (str(path), algorithm, size, mtime_ns, digest),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> SQLiteHashCache:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
