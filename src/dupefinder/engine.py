"""Integration-ready scan engine."""
from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

from dupefinder.errors import _ScanCancelled
from dupefinder.events import ScanEvent, ScanProgress
from dupefinder.grouping import candidate_files, group_by_size, groups_from_hash_map
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
            on_progress=lambda p: print(p.phase, p.scanned_files),
        )
        report = finder.scan("./uploads")
    """

    def __init__(
        self,
        options: ScanOptions | None = None,
        on_event: Callable[[ScanEvent], None] | None = None,
        on_progress: Callable[[ScanProgress], None] | None = None,
        cache: object | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> None:
        self._options = options or ScanOptions()
        self._on_event = on_event
        self._on_progress = on_progress
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
        issues_cursor = 0  # watermark: issues[issues_cursor:] are new

        # --- Phase 1: file discovery ---
        for file_info in iter_files(root, self._options, issues):
            files.append(file_info)
            self._emit(ScanEvent(
                type="file_discovered",
                root=root,
                path=file_info.path,
                scanned_files=len(files),
            ))
            self._emit_new_issues(issues, issues_cursor, root)
            issues_cursor = len(issues)
            self._progress(root, "discovery", len(files), 0, 0, 0, started_at)

            if self._is_cancelled(started_at):
                return self._build_report(
                    root, files, (), 0, issues, started_at, cancelled=True, bytes_read=0
                )
            if self._options.max_files is not None and len(files) >= self._options.max_files:
                break

        # Emit any remaining discovery issues
        self._emit_new_issues(issues, issues_cursor, root)
        issues_cursor = len(issues)

        # --- Phase 2: group by size ---
        by_size = group_by_size(files)
        candidates = candidate_files(by_size)

        # --- Phase 3: hash candidates ---
        hashed_count = 0
        total_bytes_read = 0
        by_hash: dict[tuple[int, str], list[Path]] = defaultdict(list)

        def on_bytes_read(n: int) -> None:
            nonlocal total_bytes_read
            total_bytes_read += n

        try:
            for file_info in hash_files(
                candidates,
                self._options,
                issues,
                cache=self._cache,
                should_cancel=lambda: self._is_cancelled(started_at),
                on_bytes_read=on_bytes_read,
            ):
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
                self._emit_new_issues(issues, issues_cursor, root)
                issues_cursor = len(issues)
                self._progress(root, "hashing", len(files), hashed_count, len(candidates), 0, started_at)

                if self._is_cancelled(started_at):
                    return self._build_report(
                        root, files, (), hashed_count, issues, started_at, cancelled=True, bytes_read=total_bytes_read
                    )
        except _ScanCancelled:
            self._emit_new_issues(issues, issues_cursor, root)
            issues_cursor = len(issues)
            return self._build_report(
                root, files, (), hashed_count, issues, started_at, cancelled=True, bytes_read=total_bytes_read
            )

        self._emit_new_issues(issues, issues_cursor, root)
        issues_cursor = len(issues)

        # --- Phase 4: build duplicate groups ---
        groups = tuple(groups_from_hash_map(by_hash))
        for group in groups:
            self._emit(ScanEvent(type="duplicate_group_found", root=root, group=group))

        return self._build_report(
            root, files, groups, hashed_count, issues, started_at, cancelled=False, bytes_read=total_bytes_read
        )

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

    def _emit_new_issues(
        self,
        issues: list[ScanIssue],
        cursor: int,
        root: Path,
    ) -> None:
        """Emit issue events for any issues added since cursor."""
        for issue in issues[cursor:]:
            self._emit(ScanEvent(
                type="issue",
                root=root,
                path=issue.path,
                issue=issue,
                message=issue.message,
            ))

    def _progress(
        self,
        root: Path,
        phase: str,
        scanned_files: int,
        hashed_files: int,
        total_candidates: int,
        duplicate_groups: int,
        started_at: float,
    ) -> None:
        if self._on_progress is None:
            return
        self._on_progress(ScanProgress(
            root=root,
            phase=phase,
            scanned_files=scanned_files,
            hashed_files=hashed_files,
            total_candidates=total_candidates,
            duplicate_groups=duplicate_groups,
            elapsed_seconds=time.monotonic() - started_at,
        ))

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
        bytes_read: int,
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
            total_bytes_read=bytes_read,
        )
        if self._on_progress is not None:
            self._on_progress(ScanProgress(
                root=root,
                phase="done",
                scanned_files=report.scanned_files,
                hashed_files=report.hashed_files,
                duplicate_groups=report.total_groups,
                elapsed_seconds=elapsed,
                cancelled=cancelled,
            ))
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
