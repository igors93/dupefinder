import json
import tempfile
import unittest
from pathlib import Path

from dupefinder import scan
from dupefinder.models import ScanOptions
from dupefinder.report import format_report, report_to_dict, report_to_json


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


if __name__ == "__main__":
    unittest.main()
