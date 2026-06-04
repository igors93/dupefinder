import unittest
from pathlib import Path

from dupefinder.filters import should_ignore_directory, should_ignore_file
from dupefinder.models import ScanOptions


class FilterFileTests(unittest.TestCase):
    def test_ignored_extension_is_skipped(self):
        options = ScanOptions(ignored_extensions=frozenset({".log"}), ignore_hidden=False)

        self.assertTrue(should_ignore_file(Path("app.log"), 100, options))
        self.assertFalse(should_ignore_file(Path("app.txt"), 100, options))

    def test_include_extensions_only_allows_selected_extensions(self):
        options = ScanOptions(include_extensions=frozenset({".jpg"}), ignore_hidden=False)

        self.assertFalse(should_ignore_file(Path("photo.jpg"), 100, options))
        self.assertTrue(should_ignore_file(Path("notes.txt"), 100, options))

    def test_max_size_is_respected(self):
        options = ScanOptions(max_size=10, ignore_hidden=False)

        self.assertFalse(should_ignore_file(Path("small.bin"), 10, options))
        self.assertTrue(should_ignore_file(Path("large.bin"), 11, options))

    def test_min_size_excludes_empty_files(self):
        options = ScanOptions(min_size=1, ignore_hidden=False)

        self.assertTrue(should_ignore_file(Path("empty.txt"), 0, options))
        self.assertFalse(should_ignore_file(Path("nonempty.txt"), 1, options))

    def test_hidden_file_is_ignored_by_default(self):
        options = ScanOptions(ignore_hidden=True)

        self.assertTrue(should_ignore_file(Path("/home/user/.bashrc"), 100, options))
        self.assertFalse(should_ignore_file(Path("/home/user/notes.txt"), 100, options))

    def test_hidden_file_allowed_when_ignore_hidden_false(self):
        options = ScanOptions(ignore_hidden=False)

        self.assertFalse(should_ignore_file(Path(".hidden"), 10, options))


class FilterDirectoryTests(unittest.TestCase):
    def test_root_is_never_ignored(self):
        options = ScanOptions()

        self.assertFalse(should_ignore_directory(Path(".git"), options, is_root=True))

    def test_ignored_dir_name_is_skipped(self):
        options = ScanOptions()

        self.assertTrue(should_ignore_directory(Path("some/path/__pycache__"), options))
        self.assertTrue(should_ignore_directory(Path("project/node_modules"), options))

    def test_regular_dir_is_not_ignored(self):
        options = ScanOptions(ignore_hidden=False)

        self.assertFalse(should_ignore_directory(Path("src/utils"), options))

    def test_hidden_dir_ignored_by_default(self):
        options = ScanOptions(ignore_hidden=True)

        self.assertTrue(should_ignore_directory(Path(".mydir"), options))

    def test_hidden_dir_allowed_when_ignore_hidden_false(self):
        options = ScanOptions(ignore_hidden=False)

        self.assertFalse(should_ignore_directory(Path(".mydir"), options))


if __name__ == "__main__":
    unittest.main()
