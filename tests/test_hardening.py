"""Regression tests for the hardening package."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import get_type_hints
from unittest.mock import patch

from dupefinder import DupeFinder, ScanOptions
from dupefinder.cache import SQLiteHashCache
from dupefinder.cli import main
from dupefinder.errors import InvalidPathError
from dupefinder.events import EventType, ProgressPhase, ScanEvent, ScanProgress
from dupefinder.models import ScanReport


class RootSymlinkSafetyTests(unittest.TestCase):
    def _make_dir_symlink(self, link: Path, target: Path) -> None:
        try:
            link.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Symlinks unavailable: {exc}")

    def _make_file_symlink(self, link: Path, target: Path) -> None:
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Symlinks unavailable: {exc}")

    def test_root_directory_symlink_rejected_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target"
            target.mkdir()
            (target / "file.txt").write_text("data", encoding="utf-8")
            link = root / "link"
            self._make_dir_symlink(link, target)

            with self.assertRaises(InvalidPathError):
                DupeFinder().scan(link)

    def test_root_directory_symlink_allowed_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target"
            target.mkdir()
            (target / "file.txt").write_text("data", encoding="utf-8")
            link = root / "link"
            self._make_dir_symlink(link, target)

            report = DupeFinder(ScanOptions(follow_symlinks=True)).scan(link)
            self.assertEqual(report.scanned_files, 1)

    def test_root_file_symlink_rejected_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real_file = root / "real.txt"
            real_file.write_text("data", encoding="utf-8")
            link = root / "link.txt"
            self._make_file_symlink(link, real_file)

            with self.assertRaises(InvalidPathError):
                DupeFinder().scan(link)

    def test_root_file_symlink_allowed_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real_file = root / "real.txt"
            real_file.write_text("data", encoding="utf-8")
            link = root / "link.txt"
            self._make_file_symlink(link, real_file)

            report = DupeFinder(ScanOptions(follow_symlinks=True)).scan(link)
            self.assertEqual(report.scanned_files, 1)

    def test_broken_symlink_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            link = root / "broken"
            try:
                link.symlink_to(root / "nonexistent")
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"Symlinks unavailable: {exc}")

            with self.assertRaises(InvalidPathError):
                DupeFinder().scan(link)

    def test_ordinary_file_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "file.txt"
            path.write_text("data", encoding="utf-8")
            report = DupeFinder().scan(path)
            self.assertEqual(report.scanned_files, 1)

    def test_ordinary_directory_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "file.txt").write_text("data", encoding="utf-8")
            report = DupeFinder().scan(root)
            self.assertEqual(report.scanned_files, 1)


class TypingContractTests(unittest.TestCase):
    def test_scan_options_type_hints_resolve(self) -> None:
        hints = get_type_hints(ScanOptions)
        self.assertIn("include_extensions", hints)
        self.assertIn("max_size", hints)

    def test_scan_event_type_hints_resolve(self) -> None:
        hints = get_type_hints(ScanEvent)
        self.assertIn("type", hints)
        self.assertIn("root", hints)

    def test_scan_progress_type_hints_resolve(self) -> None:
        hints = get_type_hints(ScanProgress)
        self.assertIn("phase", hints)
        self.assertIn("root", hints)

    def test_event_type_valid_values(self) -> None:
        valid: tuple[EventType, ...] = (
            "scan_started",
            "file_discovered",
            "file_hashed",
            "duplicate_group_found",
            "issue",
            "scan_completed",
            "scan_cancelled",
        )
        for value in valid:
            event = ScanEvent(type=value)
            self.assertEqual(event.type, value)

    def test_progress_phase_valid_values(self) -> None:
        valid: tuple[ProgressPhase, ...] = ("discovery", "hashing", "done")
        with tempfile.TemporaryDirectory() as tmp:
            for phase in valid:
                progress = ScanProgress(root=Path(tmp), phase=phase)
                self.assertEqual(progress.phase, phase)


class CacheIsolationTests(unittest.TestCase):
    def test_cache_inside_root_is_not_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("same", encoding="utf-8")
            (root / "b.txt").write_text("same", encoding="utf-8")
            cache_path = root / "cache.sqlite"

            with SQLiteHashCache(cache_path) as cache:
                report = DupeFinder(
                    options=ScanOptions(ignore_hidden=False),
                    cache=cache,
                ).scan(root)

            self.assertEqual(report.scanned_files, 2)
            self.assertEqual(report.total_groups, 1)

    def test_cache_outside_root_is_irrelevant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scan_dir"
            root.mkdir()
            (root / "a.txt").write_text("same", encoding="utf-8")
            (root / "b.txt").write_text("same", encoding="utf-8")
            cache_path = Path(tmp) / "external_cache.sqlite"

            with SQLiteHashCache(cache_path) as cache:
                report = DupeFinder(
                    options=ScanOptions(ignore_hidden=False),
                    cache=cache,
                ).scan(root)

            self.assertEqual(report.scanned_files, 2)
            self.assertEqual(report.total_groups, 1)

    def test_wal_shm_journal_files_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("same", encoding="utf-8")
            (root / "b.txt").write_text("same", encoding="utf-8")
            cache_path = root / "cache.sqlite"
            # Create sibling files that look like SQLite auxiliary files.
            (root / "cache.sqlite-wal").write_text("wal", encoding="utf-8")
            (root / "cache.sqlite-shm").write_text("shm", encoding="utf-8")
            (root / "cache.sqlite-journal").write_text("journal", encoding="utf-8")

            with SQLiteHashCache(cache_path) as cache:
                report = DupeFinder(
                    options=ScanOptions(ignore_hidden=False),
                    cache=cache,
                ).scan(root)

            scanned_names = {p.name for group in report.groups for p in group.files}
            self.assertNotIn("cache.sqlite-wal", scanned_names)
            self.assertNotIn("cache.sqlite-shm", scanned_names)
            self.assertNotIn("cache.sqlite-journal", scanned_names)
            self.assertEqual(report.scanned_files, 2)

    def test_similarly_named_non_cache_files_are_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data.txt").write_text("same", encoding="utf-8")
            (root / "data2.txt").write_text("same", encoding="utf-8")
            # These names do NOT match any cache exclusion — they must be counted.
            (root / "other.sqlite").write_text("other", encoding="utf-8")
            (root / "notes.sqlite-wal").write_text("wal", encoding="utf-8")
            cache_path = root / "cache.sqlite"

            with SQLiteHashCache(cache_path) as cache:
                report = DupeFinder(
                    options=ScanOptions(ignore_hidden=False),
                    cache=cache,
                ).scan(root)

            # 4 user files must be scanned; only cache.sqlite is excluded.
            self.assertEqual(report.scanned_files, 4)

    def test_scan_without_cache_works_normally(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("same", encoding="utf-8")
            (root / "b.txt").write_text("same", encoding="utf-8")
            report = DupeFinder().scan(root)
            self.assertEqual(report.scanned_files, 2)
            self.assertEqual(report.total_groups, 1)

    def test_cache_excluded_through_symlinked_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real_dir = root / "real"
            real_dir.mkdir()
            (real_dir / "a.txt").write_text("same", encoding="utf-8")
            (real_dir / "b.txt").write_text("same", encoding="utf-8")
            link = root / "link"
            try:
                link.symlink_to(real_dir, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"Symlinks unavailable: {exc}")

            # Cache placed in the real directory; accessed via the symlink.
            cache_path = real_dir / "cache.sqlite"

            with SQLiteHashCache(cache_path) as cache:
                report = DupeFinder(
                    options=ScanOptions(follow_symlinks=True, ignore_hidden=False),
                    cache=cache,
                ).scan(link)

            self.assertEqual(report.scanned_files, 2)
            self.assertEqual(report.total_groups, 1)

    def test_circular_symlink_inside_root_does_not_crash_with_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("same", encoding="utf-8")
            (root / "b.txt").write_text("same", encoding="utf-8")
            loop = root / "loop"
            try:
                loop.symlink_to(loop)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"Symlinks unavailable: {exc}")
            cache_path = root / "cache.sqlite"

            with SQLiteHashCache(cache_path) as cache:
                report = DupeFinder(
                    options=ScanOptions(ignore_hidden=False),
                    cache=cache,
                ).scan(root)

            self.assertFalse(report.cancelled)
            self.assertEqual(report.scanned_files, 2)

    def test_broken_symlink_inside_root_does_not_crash_with_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("same", encoding="utf-8")
            (root / "b.txt").write_text("same", encoding="utf-8")
            broken = root / "broken"
            try:
                broken.symlink_to(root / "nonexistent_target")
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"Symlinks unavailable: {exc}")
            cache_path = root / "cache.sqlite"

            with SQLiteHashCache(cache_path) as cache:
                report = DupeFinder(
                    options=ScanOptions(ignore_hidden=False),
                    cache=cache,
                ).scan(root)

            self.assertFalse(report.cancelled)
            self.assertEqual(report.scanned_files, 2)


class CancellationExitCodeTests(unittest.TestCase):
    def _make_report(self, **kwargs: object) -> ScanReport:
        return ScanReport(
            root=Path.cwd(),
            groups=(),
            scanned_files=1,
            hashed_files=0,
            elapsed_seconds=0.01,
            total_bytes_read=0,
            **kwargs,  # type: ignore[arg-type]
        )

    def test_normal_scan_returns_exit_code_zero(self) -> None:
        report = self._make_report(cancelled=False)
        with patch("dupefinder.cli.DupeFinder.scan", return_value=report):
            self.assertEqual(main([os.curdir]), 0)

    def test_error_returns_exit_code_one(self) -> None:
        with patch("dupefinder.cli.DupeFinder.scan", side_effect=RuntimeError("boom")):
            self.assertEqual(main([os.curdir]), 1)

    def test_cancelled_scan_returns_exit_code_three(self) -> None:
        report = self._make_report(cancelled=True)
        with patch("dupefinder.cli.DupeFinder.scan", return_value=report):
            self.assertEqual(main([os.curdir, "--json"]), 3)

    def test_cancelled_has_priority_over_fail_on_duplicates(self) -> None:
        from dupefinder.models import DuplicateGroup

        group = DuplicateGroup(digest="abc", size=4, files=(Path("a.txt"), Path("b.txt")))
        report = ScanReport(
            root=Path.cwd(),
            groups=(group,),
            scanned_files=2,
            hashed_files=2,
            cancelled=True,
            elapsed_seconds=0.01,
            total_bytes_read=8,
        )
        with patch("dupefinder.cli.DupeFinder.scan", return_value=report):
            self.assertEqual(main([os.curdir, "--fail-on-duplicates"]), 3)

    def test_json_output_is_valid_when_cancelled(self) -> None:
        report = self._make_report(cancelled=True)
        captured: list[str] = []

        import builtins

        original = builtins.print

        def capturing_print(*args: object, **kwargs: object) -> None:
            if not kwargs.get("file"):
                captured.append(" ".join(str(a) for a in args))
            else:
                original(*args, **kwargs)

        with patch("dupefinder.cli.DupeFinder.scan", return_value=report):
            with patch("builtins.print", side_effect=capturing_print):
                main([os.curdir, "--json"])

        self.assertTrue(captured, "No JSON output captured")
        parsed = json.loads(captured[0])
        self.assertIn("cancelled", parsed)
        self.assertTrue(parsed["cancelled"])


if __name__ == "__main__":
    unittest.main()
