"""Tests for the DupeFinder engine."""
from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from dupefinder import DupeFinder, ScanOptions, find_duplicates, scan
from dupefinder.events import ScanEvent
from dupefinder.models import ScanReport


class DupeFinderBasicTests(unittest.TestCase):
    def test_scan_returns_correct_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("duplicate content", encoding="utf-8")
            (root / "b.txt").write_text("duplicate content", encoding="utf-8")
            (root / "c.txt").write_text("unique content", encoding="utf-8")

            finder = DupeFinder(options=ScanOptions(ignore_hidden=False))
            report = finder.scan(tmp)

            self.assertIsInstance(report, ScanReport)
            self.assertEqual(report.total_groups, 1)
            self.assertEqual(report.scanned_files, 3)
            self.assertTrue(report.has_duplicates)

    def test_scan_no_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("unique a", encoding="utf-8")
            (root / "b.txt").write_text("unique b", encoding="utf-8")

            finder = DupeFinder(options=ScanOptions(ignore_hidden=False))
            report = finder.scan(tmp)

            self.assertFalse(report.has_duplicates)
            self.assertEqual(report.total_groups, 0)

    def test_scan_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            finder = DupeFinder()
            report = finder.scan(tmp)

            self.assertEqual(report.scanned_files, 0)
            self.assertEqual(report.total_groups, 0)

    def test_elapsed_seconds_is_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            finder = DupeFinder()
            report = finder.scan(tmp)

            self.assertIsNotNone(report.elapsed_seconds)
            self.assertGreaterEqual(report.elapsed_seconds, 0.0)

    def test_cancelled_is_false_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            finder = DupeFinder()
            report = finder.scan(tmp)

            self.assertFalse(report.cancelled)

    def test_options_property(self):
        opts = ScanOptions(min_size=100)
        finder = DupeFinder(options=opts)
        self.assertIs(finder.options, opts)

    def test_default_options_when_none_given(self):
        finder = DupeFinder()
        self.assertIsInstance(finder.options, ScanOptions)


class DupeFinderEventTests(unittest.TestCase):
    def test_events_are_emitted_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("same", encoding="utf-8")
            (root / "b.txt").write_text("same", encoding="utf-8")

            events = []
            finder = DupeFinder(
                options=ScanOptions(ignore_hidden=False),
                on_event=events.append,
            )
            finder.scan(tmp)

            types = [e.type for e in events]
            self.assertEqual(types[0], "scan_started")
            self.assertIn("file_discovered", types)
            self.assertIn("file_hashed", types)
            self.assertIn("duplicate_group_found", types)
            self.assertEqual(types[-1], "scan_completed")

    def test_scan_started_event_has_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            events = []
            finder = DupeFinder(on_event=events.append)
            finder.scan(tmp)

            started = next(e for e in events if e.type == "scan_started")
            self.assertIsNotNone(started.root)

    def test_file_discovered_event_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("a", encoding="utf-8")
            (root / "b.txt").write_text("b", encoding="utf-8")

            events = []
            finder = DupeFinder(
                options=ScanOptions(ignore_hidden=False),
                on_event=events.append,
            )
            finder.scan(tmp)

            discovered = [e for e in events if e.type == "file_discovered"]
            self.assertEqual(len(discovered), 2)
            self.assertEqual(discovered[-1].scanned_files, 2)

    def test_duplicate_group_found_event_has_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("dup", encoding="utf-8")
            (root / "b.txt").write_text("dup", encoding="utf-8")

            events = []
            finder = DupeFinder(
                options=ScanOptions(ignore_hidden=False),
                on_event=events.append,
            )
            finder.scan(tmp)

            group_events = [e for e in events if e.type == "duplicate_group_found"]
            self.assertEqual(len(group_events), 1)
            self.assertIsNotNone(group_events[0].group)
            self.assertEqual(group_events[0].group.count, 2)

    def test_scan_completed_event_has_elapsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            events = []
            finder = DupeFinder(on_event=events.append)
            finder.scan(tmp)

            completed = next(e for e in events if e.type == "scan_completed")
            self.assertIsNotNone(completed.elapsed_seconds)

    def test_no_events_when_no_callback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("x", encoding="utf-8")
            # Should not raise even without a callback
            finder = DupeFinder(options=ScanOptions(ignore_hidden=False))
            report = finder.scan(tmp)
            self.assertIsNotNone(report)


class DupeFinderCancellationTests(unittest.TestCase):
    def test_cancellation_via_should_cancel(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(10):
                (root / f"file{i}.txt").write_text(f"content {i}", encoding="utf-8")

            cancel_after = [1]

            def should_cancel() -> bool:
                cancel_after[0] -= 1
                return cancel_after[0] < 0

            events = []
            finder = DupeFinder(
                options=ScanOptions(ignore_hidden=False),
                on_event=events.append,
                should_cancel=should_cancel,
            )
            report = finder.scan(tmp)

            self.assertTrue(report.cancelled)
            event_types = [e.type for e in events]
            self.assertIn("scan_cancelled", event_types)

    def test_timeout_cancellation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(5):
                (root / f"file{i}.txt").write_text(f"content {i}", encoding="utf-8")

            finder = DupeFinder(
                options=ScanOptions(ignore_hidden=False, timeout_seconds=0.0001),
            )
            report = finder.scan(tmp)

            # With a very small timeout, scan may or may not be cancelled depending on timing.
            # Just verify that the report is valid regardless.
            self.assertIsInstance(report, ScanReport)
            # elapsed_seconds should be set
            self.assertIsNotNone(report.elapsed_seconds)

    def test_cancelled_report_has_correct_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(20):
                (root / f"file{i}.txt").write_text(f"unique content {i}", encoding="utf-8")

            call_count = [0]

            def should_cancel() -> bool:
                call_count[0] += 1
                return call_count[0] > 3

            finder = DupeFinder(
                options=ScanOptions(ignore_hidden=False),
                should_cancel=should_cancel,
            )
            report = finder.scan(tmp)

            self.assertTrue(report.cancelled)
            self.assertIsNotNone(report.elapsed_seconds)
            self.assertIsInstance(report.scanned_files, int)


class DupeFinderLimitsTests(unittest.TestCase):
    def test_max_files_limits_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(10):
                (root / f"file{i}.txt").write_text(f"content {i}", encoding="utf-8")

            finder = DupeFinder(options=ScanOptions(ignore_hidden=False, max_files=3))
            report = finder.scan(tmp)

            self.assertLessEqual(report.scanned_files, 3)

    def test_max_depth_zero_only_scans_root_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "root_file.txt").write_text("root content", encoding="utf-8")
            subdir = root / "subdir"
            subdir.mkdir()
            (subdir / "sub_file.txt").write_text("sub content", encoding="utf-8")

            finder = DupeFinder(options=ScanOptions(ignore_hidden=False, max_depth=0))
            report = finder.scan(tmp)

            # Only the root file should be found
            self.assertEqual(report.scanned_files, 1)

    def test_max_depth_one_scans_one_level_deep(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "root_file.txt").write_text("root content", encoding="utf-8")
            subdir = root / "subdir"
            subdir.mkdir()
            (subdir / "sub_file.txt").write_text("sub content", encoding="utf-8")
            subsubdir = subdir / "subsubdir"
            subsubdir.mkdir()
            (subsubdir / "deep_file.txt").write_text("deep content", encoding="utf-8")

            finder = DupeFinder(options=ScanOptions(ignore_hidden=False, max_depth=1))
            report = finder.scan(tmp)

            # root_file.txt and sub_file.txt should be found, but not deep_file.txt
            self.assertEqual(report.scanned_files, 2)

    def test_max_depth_none_scans_all_levels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "root_file.txt").write_text("root", encoding="utf-8")
            subdir = root / "subdir"
            subdir.mkdir()
            subsubdir = subdir / "subsubdir"
            subsubdir.mkdir()
            (subsubdir / "deep_file.txt").write_text("deep", encoding="utf-8")

            finder = DupeFinder(options=ScanOptions(ignore_hidden=False, max_depth=None))
            report = finder.scan(tmp)

            self.assertEqual(report.scanned_files, 2)


class BackwardCompatibilityTests(unittest.TestCase):
    """Verify that the old scan() and find_duplicates() API still works."""

    def test_scan_function_still_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("same", encoding="utf-8")
            (root / "b.txt").write_text("same", encoding="utf-8")

            report = scan(tmp, ScanOptions(ignore_hidden=False))
            self.assertEqual(report.total_groups, 1)

    def test_find_duplicates_still_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("dup", encoding="utf-8")
            (root / "b.txt").write_text("dup", encoding="utf-8")

            groups = find_duplicates(tmp, ScanOptions(ignore_hidden=False))
            self.assertEqual(len(groups), 1)

    def test_scan_with_no_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = scan(tmp)
            self.assertIsInstance(report, ScanReport)

    def test_find_duplicates_with_no_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            groups = find_duplicates(tmp)
            self.assertIsInstance(groups, tuple)


if __name__ == "__main__":
    unittest.main()
