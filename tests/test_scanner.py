import tempfile
import unittest
from pathlib import Path

from dupefinder.models import ScanOptions
from dupefinder.scanner import iter_files


class ScannerTests(unittest.TestCase):
    def test_iter_files_finds_regular_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "a.txt").write_text("a", encoding="utf-8")
            (root / "nested").mkdir()
            (root / "nested" / "b.txt").write_text("b", encoding="utf-8")

            found = list(iter_files(root, ScanOptions(ignore_hidden=False)))
            names = sorted(path_info.path.name for path_info in found)

            self.assertEqual(names, ["a.txt", "b.txt"])

    def test_iter_files_ignores_hidden_by_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".hidden.txt").write_text("secret", encoding="utf-8")
            (root / "visible.txt").write_text("ok", encoding="utf-8")

            found = list(iter_files(root, ScanOptions()))
            names = [path_info.path.name for path_info in found]

            self.assertEqual(names, ["visible.txt"])

    def test_iter_files_respects_min_size(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "small.txt").write_text("a", encoding="utf-8")
            (root / "large.txt").write_text("abc", encoding="utf-8")

            found = list(iter_files(root, ScanOptions(min_size=2, ignore_hidden=False)))
            names = [path_info.path.name for path_info in found]

            self.assertEqual(names, ["large.txt"])


if __name__ == "__main__":
    unittest.main()
