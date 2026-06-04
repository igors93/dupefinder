import tempfile
import unittest
from pathlib import Path

from dupefinder import find_duplicates, scan
from dupefinder.grouping import group_by_size
from dupefinder.models import FileInfo, ScanOptions


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

    def test_wasted_space_calculation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            content = "x" * 100
            (root / "a.txt").write_text(content, encoding="utf-8")
            (root / "b.txt").write_text(content, encoding="utf-8")
            (root / "c.txt").write_text(content, encoding="utf-8")

            groups = find_duplicates(root, ScanOptions(ignore_hidden=False))

            self.assertEqual(len(groups), 1)
            group = groups[0]
            self.assertEqual(group.count, 3)
            self.assertEqual(group.wasted_space, group.size * 2)

    def test_no_duplicates_returns_empty_tuple(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "a.txt").write_text("unique1", encoding="utf-8")
            (root / "b.txt").write_text("unique22", encoding="utf-8")

            groups = find_duplicates(root, ScanOptions(ignore_hidden=False))

            self.assertEqual(groups, ())

    def test_group_by_size_separates_different_sizes(self):
        files = [
            FileInfo(path=Path("a.txt"), size=10),
            FileInfo(path=Path("b.txt"), size=10),
            FileInfo(path=Path("c.txt"), size=20),
        ]
        grouped = group_by_size(files)

        self.assertEqual(len(grouped[10]), 2)
        self.assertEqual(len(grouped[20]), 1)

    def test_duplicate_groups_are_sorted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "a.txt").write_text("xx", encoding="utf-8")
            (root / "b.txt").write_text("xx", encoding="utf-8")
            (root / "c.txt").write_text("yyyy", encoding="utf-8")
            (root / "d.txt").write_text("yyyy", encoding="utf-8")

            report = scan(root, ScanOptions(ignore_hidden=False))
            sizes = [g.size for g in report.groups]

            self.assertEqual(sizes, sorted(sizes))


if __name__ == "__main__":
    unittest.main()
