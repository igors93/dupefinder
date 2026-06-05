"""Tests for model to_dict() and to_json() methods."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dupefinder import scan
from dupefinder.models import DuplicateGroup, ScanIssue, ScanOptions, ScanReport


class ScanReportDictTests(unittest.TestCase):
    def _make_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("same", encoding="utf-8")
            (root / "b.txt").write_text("same", encoding="utf-8")
            return scan(root, ScanOptions(ignore_hidden=False))

    def test_to_dict_returns_dict(self):
        report = self._make_report()
        result = report.to_dict()
        self.assertIsInstance(result, dict)

    def test_to_dict_contains_expected_keys(self):
        report = self._make_report()
        result = report.to_dict()
        expected_keys = [
            "schema_version",
            "root",
            "scanned_files",
            "hashed_files",
            "total_groups",
            "total_duplicate_files",
            "total_wasted_space",
            "cancelled",
            "elapsed_seconds",
            "groups",
            "issues",
        ]
        for key in expected_keys:
            self.assertIn(key, result)

    def test_to_json_is_valid_json(self):
        report = self._make_report()
        result = report.to_json()
        parsed = json.loads(result)
        self.assertIsInstance(parsed, dict)

    def test_to_json_indent_none_produces_compact_json(self):
        report = self._make_report()
        result = report.to_json(indent=None)
        # compact JSON has no newlines
        self.assertNotIn("\n", result)

    def test_cancelled_report_has_cancelled_true_in_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = ScanReport(
                root=root,
                groups=(),
                scanned_files=0,
                hashed_files=0,
                cancelled=True,
            )
            result = report.to_dict()
            self.assertTrue(result["cancelled"])

    def test_non_cancelled_report_has_cancelled_false_in_dict(self):
        report = self._make_report()
        result = report.to_dict()
        self.assertFalse(result["cancelled"])


class DuplicateGroupDictTests(unittest.TestCase):
    def _make_group(self) -> DuplicateGroup:
        return DuplicateGroup(
            digest="abc123",
            size=1024,
            files=(Path("/a/file1.txt"), Path("/a/file2.txt")),
        )

    def test_to_dict_returns_dict(self):
        group = self._make_group()
        result = group.to_dict()
        self.assertIsInstance(result, dict)

    def test_to_dict_contains_expected_keys(self):
        group = self._make_group()
        result = group.to_dict()
        for key in ("digest", "size", "count", "wasted_space", "files"):
            self.assertIn(key, result)

    def test_to_dict_values_are_correct(self):
        group = self._make_group()
        result = group.to_dict()
        self.assertEqual(result["digest"], "abc123")
        self.assertEqual(result["size"], 1024)
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["wasted_space"], 1024)
        self.assertEqual(len(result["files"]), 2)

    def test_to_dict_paths_are_strings(self):
        group = self._make_group()
        result = group.to_dict()
        for f in result["files"]:
            self.assertIsInstance(f, str)


class ScanIssueDictTests(unittest.TestCase):
    def _make_issue(self) -> ScanIssue:
        return ScanIssue(
            path=Path("/some/file.txt"),
            message="Permission denied",
            phase="scan",
        )

    def test_to_dict_returns_dict(self):
        issue = self._make_issue()
        result = issue.to_dict()
        self.assertIsInstance(result, dict)

    def test_to_dict_contains_expected_keys(self):
        issue = self._make_issue()
        result = issue.to_dict()
        for key in ("path", "message", "phase"):
            self.assertIn(key, result)

    def test_to_dict_values_are_correct(self):
        issue = self._make_issue()
        result = issue.to_dict()
        self.assertEqual(result["path"], str(Path("/some/file.txt")))
        self.assertEqual(result["message"], "Permission denied")
        self.assertEqual(result["phase"], "scan")

    def test_to_dict_path_is_string(self):
        issue = self._make_issue()
        result = issue.to_dict()
        self.assertIsInstance(result["path"], str)


if __name__ == "__main__":
    unittest.main()
