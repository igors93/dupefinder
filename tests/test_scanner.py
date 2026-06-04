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

    def test_iter_files_skips_ignored_dirs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "__pycache__").mkdir()
            (root / "__pycache__" / "cached.pyc").write_bytes(b"\x00")
            (root / "main.py").write_text("pass", encoding="utf-8")

            found = list(iter_files(root, ScanOptions(ignore_hidden=False)))
            names = [path_info.path.name for path_info in found]

            self.assertEqual(names, ["main.py"])

    def test_iter_files_respects_include_extensions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "photo.jpg").write_bytes(b"\xff")
            (root / "notes.txt").write_text("hi", encoding="utf-8")

            options = ScanOptions(include_extensions=frozenset({".jpg"}), ignore_hidden=False)
            found = list(iter_files(root, options))
            names = [f.path.name for f in found]

            self.assertEqual(names, ["photo.jpg"])

    def test_iter_single_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "single.txt"
            file_path.write_text("hello", encoding="utf-8")

            found = list(iter_files(file_path, ScanOptions(ignore_hidden=False)))

            self.assertEqual(len(found), 1)
            self.assertEqual(found[0].path, file_path)

    def test_iter_files_records_issues_on_access_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "ok.txt").write_text("data", encoding="utf-8")

            issues: list = []
            options = ScanOptions(ignore_hidden=False, on_error="skip")
            list(iter_files(root, options, issues))

            self.assertEqual(len(issues), 0)


if __name__ == "__main__":
    unittest.main()
