import unittest
from pathlib import Path

from dupefinder.filters import should_ignore_file
from dupefinder.models import ScanOptions


class FilterTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
