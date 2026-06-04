"""Integration-ready scan engine."""
from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

from dupefinder.events import ScanEvent
from dupefinder.hashing import hash_files
from dupefinder.models import DuplicateGroup, FileInfo, ScanIssue, ScanOptions, ScanReport
from dupefinder.safety import validate_options, validate_scan_path
from dupefinder.scanner import iter_files


class DupeFinder:
    """Integration-ready duplicate file detection engine.

    Encapsulates scan options, an optional event callback, an optional hash
    cache, and an optional cancellation hook. The scan pipeline emits typed
    events so host applications can observe progress without polling.

    Usage::

        from dupefinder import DupeFinder, ScanOptions

        finder = DupeFinder(
            options=ScanOptions(min_size=1024),
            on_event=lambda event: print(event.type, event.scanned_files),
        )
        report = finder.scan("./uploads")
    """

    def __init__(
        self,
        options: ScanOptions | None = None,
        on_event: Callable[[ScanEvent], None] | None = None,
        cache: object | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> None:
        self._options = options or ScanOptions()
        self._on_event = on_event
        self._cache = cache
        self._should_cancel = should_cancel

    @property
    def options(self) -> ScanOptions:
        return self._options

    def scan(self, path: str | Path) -> ScanReport:
        """Scan a path and return a complete report.

        Emits events throughout the scan. If ``should_cancel`` returns
        ``True`` or ``timeout_seconds`` is exceeded, returns a partial report
        with ``cancelled=True``.
        """
        validate_options(self._options)
        root = validate_scan_path(path)
        started_at = time.monotonic()

        self._emit(ScanEvent(type="scan_started", root=root))

        issues: list[ScanIssue] = []
        files: list[FileInfo] = []

        # --- Phase 1: file discovery ---
        for file_info in iter_files(root, self._options, issues):
            files.append(file_info)
            self._emit(ScanEvent(
                type="file_discovered",
                root=root,
                path=file_info.path,
                scanned_files=len(files),
            ))
            if self._is_cancelled(started_at):
                return self._build_report(root, files, (), 0, issues, started_at, cancelled=True)
            if self._options.max_files is not None and len(files) >= self._options.max_files:
                break

        # --- Phase 2: group by size ---
        by_size: dict[int, list[FileInfo]] = defaultdict(list)
        for f in files:
            by_size[f.size].append(f)
        candidates = [
            f for same_size in by_size.values() if len(same_size) > 1 for f in same_size
        ]

        # --- Phase 3: hash candidates ---
        hashed_count = 0
        by_hash: dict[tuple[int, str], list[Path]] = defaultdict(list)

        for file_info in hash_files(candidates, self._options, issues, cache=self._cache):
            assert file_info.digest is not None
            hashed_count += 1
            by_hash[(file_info.size, file_info.digest)].append(file_info.path)
            self._emit(ScanEvent(
                type="file_hashed",
                root=root,
                path=file_info.path,
                hashed_files=hashed_count,
                total_candidates=len(candidates),
            ))
            if self._is_cancelled(started_at):
                return self._build_report(root, files, (), hashed_count, issues, started_at, cancelled=True)

        # --- Phase 4: build duplicate groups ---
        groups_list: list[DuplicateGroup] = []
        for (size, digest), paths in by_hash.items():
            if len(paths) > 1:
                group = DuplicateGroup(
                    digest=digest,
                    size=size,
                    files=tuple(sorted(paths)),
                )
                groups_list.append(group)
                self._emit(ScanEvent(type="duplicate_group_found", root=root, group=group))

        groups_list.sort(key=lambda g: (g.size, g.digest, tuple(str(p) for p in g.files)))
        groups = tuple(groups_list)

        return self._build_report(root, files, groups, hashed_count, issues, started_at, cancelled=False)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _is_cancelled(self, started_at: float) -> bool:
        if self._should_cancel is not None and self._should_cancel():
            return True
        timeout = self._options.timeout_seconds
        if timeout is not None and time.monotonic() - started_at > timeout:
            return True
        return False

    def _build_report(
        self,
        root: Path,
        files: list[FileInfo],
        groups: tuple[DuplicateGroup, ...],
        hashed_files: int,
        issues: list[ScanIssue],
        started_at: float,
        *,
        cancelled: bool,
    ) -> ScanReport:
        elapsed = time.monotonic() - started_at
        report = ScanReport(
            root=root,
            groups=groups,
            scanned_files=len(files),
            hashed_files=hashed_files,
            issues=tuple(issues),
            cancelled=cancelled,
            elapsed_seconds=elapsed,
        )
        self._emit(ScanEvent(
            type="scan_cancelled" if cancelled else "scan_completed",
            root=root,
            scanned_files=report.scanned_files,
            hashed_files=report.hashed_files,
            duplicate_groups=report.total_groups,
            elapsed_seconds=elapsed,
        ))
        return report

    def _emit(self, event: ScanEvent) -> None:
        if self._on_event is not None:
            self._on_event(event)
