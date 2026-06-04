import tempfile
import unittest
from pathlib import Path

from dupefinder import find_duplicates, scan
from dupefinder.models import ScanOptions


class GroupingTests(unittest.TestCase):
    def test_find_duplicates_returns_duplicate_group(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "a.txt").write_text("same", encoding="utf-8")
            (root / "b.txt").write_text("same", encoding="utf-8")
            (root / "c.txt").write_text("different", encoding="utf-8")

            groups = find_duplicates(root, ScanOptions(ignore_hidden=False))

            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0].count, 2)
            self.assertEqual({path.name for path in groups[0].files}, {"a.txt", "b.txt"})

    def test_unique_size_files_are_not_hashed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "a.txt").write_text("a", encoding="utf-8")
            (root / "bb.txt").write_text("bb", encoding="utf-8")
            (root / "ccc.txt").write_text("ccc", encoding="utf-8")

            report = scan(root, ScanOptions(ignore_hidden=False))

            self.assertEqual(report.has_duplicates, False)
            self.assertEqual(report.hashed_files, 0)


if __name__ == "__main__":
    unittest.main()
