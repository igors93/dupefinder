"""Regression tests for the five-point hardening package."""
from __future__ import annotations

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
from dupefinder.events import ScanEvent, ScanProgress
from dupefinder.models import ScanReport


class RootSymlinkSafetyTests(unittest.TestCase):
    def _make_directory_symlink(self, link: Path, target: Path) -> None:
        try:
            link.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Symlinks are not available: {exc}")

    def test_root_symlink_is_rejected_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "target"
            target.mkdir()
            (target / "file.txt").write_text("data", encoding="utf-8")
            link = root / "link"
            self._make_directory_symlink(link, target)

            with self.assertRaises(InvalidPathError):
                DupeFinder().scan(link)

    def test_root_symlink_is_allowed_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "target"
            target.mkdir()
            (target / "file.txt").write_text("data", encoding="utf-8")
            link = root / "link"
            self._make_directory_symlink(link, target)

            report = DupeFinder(ScanOptions(follow_symlinks=True)).scan(link)
            self.assertEqual(report.scanned_files, 1)


class TypingContractTests(unittest.TestCase):
    def test_public_type_hints_can_be_resolved(self) -> None:
        self.assertIn("include_extensions", get_type_hints(ScanOptions))
        self.assertIn("type", get_type_hints(ScanEvent))
        self.assertIn("phase", get_type_hints(ScanProgress))


class CacheIsolationTests(unittest.TestCase):
    def test_sqlite_cache_inside_root_is_not_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
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


class CancellationExitCodeTests(unittest.TestCase):
    def test_cancelled_scan_returns_exit_code_three(self) -> None:
        report = ScanReport(
            root=Path.cwd(),
            groups=(),
            scanned_files=1,
            hashed_files=0,
            cancelled=True,
            elapsed_seconds=0.01,
            total_bytes_read=0,
        )
        with patch("dupefinder.cli.DupeFinder.scan", return_value=report):
            exit_code = main([os.curdir, "--json"])
        self.assertEqual(exit_code, 3)


if __name__ == "__main__":
    unittest.main()
