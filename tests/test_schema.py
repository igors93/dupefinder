"""Tests for JSON schema versioning."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dupefinder import scan
from dupefinder.constants import SCHEMA_VERSION
from dupefinder.models import ScanOptions
from dupefinder.report import report_to_dict, report_to_json


class SchemaVersionTests(unittest.TestCase):
    def _make_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            return scan(root, ScanOptions(ignore_hidden=False))

    def test_schema_version_constant_is_correct(self):
        self.assertEqual(SCHEMA_VERSION, "1.1")

    def test_report_to_dict_includes_schema_version(self):
        report = self._make_report()
        data = report_to_dict(report)
        self.assertIn("schema_version", data)
        self.assertEqual(data["schema_version"], "1.1")

    def test_report_to_json_includes_schema_version(self):
        report = self._make_report()
        json_str = report_to_json(report)
        parsed = json.loads(json_str)
        self.assertIn("schema_version", parsed)
        self.assertEqual(parsed["schema_version"], "1.1")

    def test_report_to_dict_schema_version_is_string(self):
        report = self._make_report()
        data = report_to_dict(report)
        self.assertIsInstance(data["schema_version"], str)

    def test_to_dict_method_includes_schema_version(self):
        report = self._make_report()
        data = report.to_dict()
        self.assertEqual(data["schema_version"], "1.1")

    def test_to_json_method_includes_schema_version(self):
        report = self._make_report()
        json_str = report.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["schema_version"], "1.1")


if __name__ == "__main__":
    unittest.main()
