import json
import tempfile
import unittest
from pathlib import Path

from dupefinder import scan
from dupefinder.models import ScanOptions
from dupefinder.report import bytes_to_human, format_report, report_to_dict, report_to_json


class ReportTests(unittest.TestCase):
    def test_report_can_be_serialized_to_dict_and_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "a.txt").write_text("same", encoding="utf-8")
            (root / "b.txt").write_text("same", encoding="utf-8")

            report = scan(root, ScanOptions(ignore_hidden=False))
            data = report_to_dict(report)
            json_data = json.loads(report_to_json(report))

            self.assertEqual(data["total_groups"], 1)
            self.assertEqual(json_data["total_groups"], 1)

    def test_format_report_mentions_no_duplicates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "a.txt").write_text("a", encoding="utf-8")

            report = scan(root, ScanOptions(ignore_hidden=False))
            text = format_report(report)

            self.assertIn("No duplicates found", text)

    def test_format_report_lists_duplicate_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "a.txt").write_text("same", encoding="utf-8")
            (root / "b.txt").write_text("same", encoding="utf-8")

            report = scan(root, ScanOptions(ignore_hidden=False))
            text = format_report(report)

            self.assertIn("a.txt", text)
            self.assertIn("b.txt", text)

    def test_report_to_dict_contains_expected_keys(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = scan(root, ScanOptions(ignore_hidden=False))
            data = report_to_dict(report)

            for key in ("root", "scanned_files", "hashed_files", "total_groups",
                        "total_duplicate_files", "total_wasted_space", "groups", "issues"):
                self.assertIn(key, data)

    def test_report_to_json_is_valid_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = scan(root, ScanOptions(ignore_hidden=False))
            result = report_to_json(report)

            parsed = json.loads(result)
            self.assertIsInstance(parsed, dict)


class BytesToHumanTests(unittest.TestCase):
    def test_bytes(self):
        self.assertEqual(bytes_to_human(0), "0 B")
        self.assertEqual(bytes_to_human(999), "999 B")

    def test_kilobytes(self):
        self.assertEqual(bytes_to_human(1000), "1.00 KB")
        self.assertEqual(bytes_to_human(1500), "1.50 KB")

    def test_megabytes(self):
        self.assertEqual(bytes_to_human(1_000_000), "1.00 MB")

    def test_gigabytes(self):
        self.assertEqual(bytes_to_human(1_000_000_000), "1.00 GB")

    def test_terabytes(self):
        self.assertEqual(bytes_to_human(1_000_000_000_000), "1.00 TB")

    def test_large_terabytes(self):
        result = bytes_to_human(5_000_000_000_000)
        self.assertIn("TB", result)


if __name__ == "__main__":
    unittest.main()
