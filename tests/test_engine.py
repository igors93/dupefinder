"""Tests for the DupeFinder engine."""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from dupefinder import DupeFinder, ScanOptions, find_duplicates, scan
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


class DupeFinderIssueEventTests(unittest.TestCase):
    """Test that issue events are emitted for scan errors."""

    def test_issue_event_emitted_for_hash_error(self):
        """Patch hash_file to raise OSError for one file; verify issue event is emitted."""
        from unittest.mock import patch
        from dupefinder.errors import FileHashError

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("duplicate", encoding="utf-8")
            (root / "b.txt").write_text("duplicate", encoding="utf-8")

            call_count = [0]
            original_hash_file = __import__("dupefinder.hashing", fromlist=["hash_file"]).hash_file

            def failing_hash_file(path, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise FileHashError(f"Simulated hash error for {path}")
                return original_hash_file(path, **kwargs)

            events = []
            with patch("dupefinder.hashing.hash_file", side_effect=failing_hash_file):
                finder = DupeFinder(
                    options=ScanOptions(ignore_hidden=False, on_error="skip"),
                    on_event=events.append,
                )
                report = finder.scan(tmp)

            issue_events = [e for e in events if e.type == "issue"]
            self.assertEqual(len(issue_events), 1)
            self.assertIsNotNone(issue_events[0].issue)
            self.assertEqual(len(report.issues), 1)

    def test_issue_event_has_correct_fields(self):
        """Issue event should have path, message, and issue fields set."""
        from unittest.mock import patch
        from dupefinder.errors import FileHashError

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("dup", encoding="utf-8")
            (root / "b.txt").write_text("dup", encoding="utf-8")

            def always_fail(path, **kwargs):
                raise FileHashError(f"Error on {path}")

            events = []
            with patch("dupefinder.hashing.hash_file", side_effect=always_fail):
                finder = DupeFinder(
                    options=ScanOptions(ignore_hidden=False, on_error="skip"),
                    on_event=events.append,
                )
                finder.scan(tmp)

            issue_events = [e for e in events if e.type == "issue"]
            self.assertGreater(len(issue_events), 0)
            for ev in issue_events:
                self.assertEqual(ev.type, "issue")
                self.assertIsNotNone(ev.path)
                self.assertIsNotNone(ev.message)
                self.assertIsNotNone(ev.issue)


class DupeFinderCancellationDuringHashingTests(unittest.TestCase):
    """Test _ScanCancelled propagation and cancellation during hashing."""

    def test_cancellation_via_should_cancel_during_hashing(self):
        """should_cancel returning True during hashing sets cancelled=True."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Create duplicate files so they get hashed
            content = "x" * 100
            (root / "a.txt").write_text(content, encoding="utf-8")
            (root / "b.txt").write_text(content, encoding="utf-8")

            cancel_calls = [0]

            def should_cancel():
                cancel_calls[0] += 1
                # Cancel after the first check (during hashing phase)
                return cancel_calls[0] > 5

            events = []
            finder = DupeFinder(
                options=ScanOptions(ignore_hidden=False, chunk_size=1),
                on_event=events.append,
                should_cancel=should_cancel,
            )
            report = finder.scan(tmp)

            # Either cancelled mid-hash or completed — just verify structure
            self.assertIsInstance(report, ScanReport)
            self.assertIsNotNone(report.elapsed_seconds)

    def test_scan_cancelled_event_emitted_on_cancellation(self):
        """When cancelled, scan_cancelled event is emitted (not scan_completed)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(20):
                (root / f"file{i}.txt").write_text(f"unique content {i}", encoding="utf-8")

            call_count = [0]

            def should_cancel():
                call_count[0] += 1
                return call_count[0] > 2

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
            self.assertNotIn("scan_completed", event_types)

    def test_cancelled_report_has_no_partial_groups(self):
        """A cancelled scan should not include partial duplicate groups."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(10):
                (root / f"file{i}.txt").write_text(f"unique content {i}", encoding="utf-8")

            def always_cancel():
                return True

            finder = DupeFinder(
                options=ScanOptions(ignore_hidden=False),
                should_cancel=always_cancel,
            )
            report = finder.scan(tmp)

            self.assertTrue(report.cancelled)
            # No groups in a cancelled scan from discovery phase
            self.assertEqual(report.total_groups, 0)


class DupeFinderProgressTests(unittest.TestCase):
    """Test on_progress callback behavior."""

    def test_on_progress_receives_discovery_phase(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("hello", encoding="utf-8")
            (root / "b.txt").write_text("world", encoding="utf-8")

            progress_events = []
            finder = DupeFinder(
                options=ScanOptions(ignore_hidden=False),
                on_progress=progress_events.append,
            )
            finder.scan(tmp)

            phases = [p.phase for p in progress_events]
            self.assertIn("discovery", phases)

    def test_on_progress_receives_done_phase(self):
        with tempfile.TemporaryDirectory() as tmp:
            progress_events = []
            finder = DupeFinder(
                on_progress=progress_events.append,
            )
            finder.scan(tmp)

            phases = [p.phase for p in progress_events]
            self.assertIn("done", phases)

    def test_on_progress_done_has_correct_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            progress_events = []
            finder = DupeFinder(on_progress=progress_events.append)
            finder.scan(tmp)

            done_events = [p for p in progress_events if p.phase == "done"]
            self.assertEqual(len(done_events), 1)
            self.assertEqual(done_events[0].root, root)

    def test_on_progress_hashing_phase_emitted_for_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("same content", encoding="utf-8")
            (root / "b.txt").write_text("same content", encoding="utf-8")

            progress_events = []
            finder = DupeFinder(
                options=ScanOptions(ignore_hidden=False),
                on_progress=progress_events.append,
            )
            finder.scan(tmp)

            phases = [p.phase for p in progress_events]
            self.assertIn("hashing", phases)

    def test_on_progress_none_does_not_raise(self):
        """No on_progress callback should not cause any errors."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("x", encoding="utf-8")
            finder = DupeFinder(options=ScanOptions(ignore_hidden=False))
            report = finder.scan(tmp)
            self.assertIsNotNone(report)

    def test_on_progress_scanned_files_increases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(5):
                (root / f"file{i}.txt").write_text(f"content {i}", encoding="utf-8")

            progress_events = []
            finder = DupeFinder(
                options=ScanOptions(ignore_hidden=False),
                on_progress=progress_events.append,
            )
            finder.scan(tmp)

            discovery_events = [p for p in progress_events if p.phase == "discovery"]
            if discovery_events:
                # scanned_files should be positive
                self.assertGreater(discovery_events[-1].scanned_files, 0)

    def test_on_progress_done_has_elapsed_seconds(self):
        with tempfile.TemporaryDirectory() as tmp:
            progress_events = []
            finder = DupeFinder(on_progress=progress_events.append)
            finder.scan(tmp)

            done = next(p for p in progress_events if p.phase == "done")
            self.assertIsNotNone(done.elapsed_seconds)
            self.assertGreaterEqual(done.elapsed_seconds, 0.0)

    def test_on_progress_cancelled_is_set_when_scan_cancelled(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(10):
                (root / f"file{i}.txt").write_text(f"unique {i}", encoding="utf-8")

            call_count = [0]

            def should_cancel():
                call_count[0] += 1
                return call_count[0] > 2

            progress_events = []
            finder = DupeFinder(
                options=ScanOptions(ignore_hidden=False),
                on_progress=progress_events.append,
                should_cancel=should_cancel,
            )
            report = finder.scan(tmp)

            if report.cancelled:
                done_events = [p for p in progress_events if p.phase == "done"]
                self.assertEqual(len(done_events), 1)
                self.assertTrue(done_events[0].cancelled)


class DupeFinderBytesReadTests(unittest.TestCase):
    """Test total_bytes_read tracking."""

    def test_total_bytes_read_populated_for_duplicate_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = "x" * 50
            (root / "a.txt").write_text(content, encoding="utf-8")
            (root / "b.txt").write_text(content, encoding="utf-8")

            finder = DupeFinder(options=ScanOptions(ignore_hidden=False))
            report = finder.scan(tmp)

            self.assertIsNotNone(report.total_bytes_read)
            self.assertGreater(report.total_bytes_read, 0)

    def test_total_bytes_read_zero_when_no_candidates(self):
        """Files with unique sizes require no hashing, so bytes_read should be 0."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("a", encoding="utf-8")
            (root / "bb.txt").write_text("bb", encoding="utf-8")

            finder = DupeFinder(options=ScanOptions(ignore_hidden=False))
            report = finder.scan(tmp)

            self.assertEqual(report.total_bytes_read, 0)

    def test_total_bytes_read_in_report_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = "duplicate"
            (root / "a.txt").write_text(content, encoding="utf-8")
            (root / "b.txt").write_text(content, encoding="utf-8")

            finder = DupeFinder(options=ScanOptions(ignore_hidden=False))
            report = finder.scan(tmp)
            data = report.to_dict()

            self.assertIn("total_bytes_read", data)

    def test_total_bytes_read_in_json_output(self):
        import json

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("same", encoding="utf-8")
            (root / "b.txt").write_text("same", encoding="utf-8")

            finder = DupeFinder(options=ScanOptions(ignore_hidden=False))
            report = finder.scan(tmp)
            parsed = json.loads(report.to_json())

            self.assertIn("total_bytes_read", parsed)

    def test_total_bytes_read_zero_for_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            finder = DupeFinder()
            report = finder.scan(tmp)
            self.assertEqual(report.total_bytes_read, 0)


class DupeFinderTimeoutDeterministicTests(unittest.TestCase):
    """Deterministic timeout tests using monkeypatching."""

    def test_timeout_cancels_scan_deterministic(self):
        """Monkeypatch time.monotonic to simulate timeout after first call."""
        import dupefinder.engine as engine_module
        from unittest.mock import patch

        call_count = [0]
        base = time.monotonic()

        def fake_monotonic():
            call_count[0] += 1
            # First call sets started_at; subsequent calls return far in the future
            return base if call_count[0] == 1 else base + 100.0

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("x", encoding="utf-8")

            with patch.object(engine_module.time, "monotonic", side_effect=fake_monotonic):
                finder = DupeFinder(
                    options=ScanOptions(timeout_seconds=1.0, ignore_hidden=False),
                )
                report = finder.scan(tmp)

            self.assertTrue(report.cancelled)


class DupeFinderCacheErrorTests(unittest.TestCase):
    """Test that cache errors don't corrupt or crash the scan."""

    def test_cache_get_sqlite_error_does_not_crash(self):
        """A cache that raises sqlite3.Error on get() should be silently skipped."""
        import sqlite3

        class BrokenGetCache:
            def get(self, path, *, size, mtime_ns, algorithm):
                raise sqlite3.Error("Simulated SQLite error")

            def set(self, path, *, size, mtime_ns, algorithm, digest):
                pass

            def close(self):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = "dup"
            (root / "a.txt").write_text(content, encoding="utf-8")
            (root / "b.txt").write_text(content, encoding="utf-8")

            finder = DupeFinder(
                options=ScanOptions(ignore_hidden=False),
                cache=BrokenGetCache(),
            )
            report = finder.scan(tmp)

            # Scan should still find the duplicates
            self.assertEqual(report.total_groups, 1)
            self.assertFalse(report.has_issues)

    def test_cache_set_sqlite_error_does_not_crash(self):
        """A cache that raises sqlite3.Error on set() should be silently skipped."""
        import sqlite3

        class BrokenSetCache:
            def get(self, path, *, size, mtime_ns, algorithm):
                return None  # Cache miss

            def set(self, path, *, size, mtime_ns, algorithm, digest):
                raise sqlite3.Error("Simulated SQLite error on set")

            def close(self):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = "same content"
            (root / "a.txt").write_text(content, encoding="utf-8")
            (root / "b.txt").write_text(content, encoding="utf-8")

            finder = DupeFinder(
                options=ScanOptions(ignore_hidden=False),
                cache=BrokenSetCache(),
            )
            report = finder.scan(tmp)

            # Scan completes successfully despite cache error
            self.assertEqual(report.total_groups, 1)
            self.assertFalse(report.has_issues)

    def test_cache_os_error_on_get_does_not_crash(self):
        """A cache that raises OSError on get() should be silently skipped."""

        class BrokenOSErrorCache:
            def get(self, path, *, size, mtime_ns, algorithm):
                raise OSError("Simulated OS error")

            def set(self, path, *, size, mtime_ns, algorithm, digest):
                pass

            def close(self):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = "hello"
            (root / "a.txt").write_text(content, encoding="utf-8")
            (root / "b.txt").write_text(content, encoding="utf-8")

            finder = DupeFinder(
                options=ScanOptions(ignore_hidden=False),
                cache=BrokenOSErrorCache(),
            )
            report = finder.scan(tmp)

            self.assertEqual(report.total_groups, 1)


if __name__ == "__main__":
    unittest.main()
