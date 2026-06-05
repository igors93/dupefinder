import tempfile
import unittest
from pathlib import Path

from dupefinder.errors import InvalidOptionError, InvalidPathError, UnsupportedHashAlgorithmError
from dupefinder.models import ScanOptions
from dupefinder.safety import (
    is_hidden_path,
    normalize_extension,
    normalize_extensions,
    normalize_path,
    validate_options,
    validate_scan_path,
)


class ValidateScanPathTests(unittest.TestCase):
    def test_rejects_missing_path(self):
        with self.assertRaises(InvalidPathError):
            validate_scan_path("/path/that/should/not/exist/dupefinder")

    def test_accepts_existing_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = validate_scan_path(temp_dir)
            self.assertTrue(result.is_absolute())
            self.assertTrue(result.exists())

    def test_accepts_existing_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "file.txt"
            file_path.write_text("x", encoding="utf-8")
            result = validate_scan_path(file_path)
            self.assertTrue(result.is_absolute())
            self.assertTrue(result.exists())

    def test_expands_home_tilde(self):
        result = normalize_path("~/nonexistent")
        self.assertNotIn("~", str(result))


class ValidateOptionsTests(unittest.TestCase):
    def test_rejects_invalid_algorithm(self):
        with self.assertRaises(UnsupportedHashAlgorithmError):
            validate_options(ScanOptions(algorithm="fake-hash"))

    def test_rejects_bad_chunk_size(self):
        with self.assertRaises(InvalidOptionError):
            validate_options(ScanOptions(chunk_size=0))

    def test_rejects_negative_min_size(self):
        with self.assertRaises(InvalidOptionError):
            validate_options(ScanOptions(min_size=-1))

    def test_rejects_max_size_smaller_than_min_size(self):
        with self.assertRaises(InvalidOptionError):
            validate_options(ScanOptions(min_size=100, max_size=50))

    def test_rejects_invalid_on_error_value(self):
        with self.assertRaises(InvalidOptionError):
            validate_options(ScanOptions(on_error="ignore"))  # type: ignore[arg-type]

    def test_accepts_valid_options(self):
        validate_options(ScanOptions())


class IsHiddenPathTests(unittest.TestCase):
    def test_dotfile_is_hidden(self):
        self.assertTrue(is_hidden_path(Path("/home/user/.bashrc")))

    def test_dotfolder_is_hidden(self):
        self.assertTrue(is_hidden_path(Path("/home/user/.config/file.txt")))

    def test_regular_path_is_not_hidden(self):
        self.assertFalse(is_hidden_path(Path("/home/user/documents/file.txt")))

    def test_dot_and_dotdot_are_not_hidden(self):
        self.assertFalse(is_hidden_path(Path("./file.txt")))
        self.assertFalse(is_hidden_path(Path("../file.txt")))


class NormalizeExtensionTests(unittest.TestCase):
    def test_normalize_extensions(self):
        self.assertEqual(
            normalize_extensions(["jpg", ".PNG", " txt "]),
            frozenset({".jpg", ".png", ".txt"}),
        )

    def test_normalize_extension_adds_dot(self):
        self.assertEqual(normalize_extension("jpg"), ".jpg")

    def test_normalize_extension_lowercases(self):
        self.assertEqual(normalize_extension(".PNG"), ".png")

    def test_normalize_extension_strips_spaces(self):
        self.assertEqual(normalize_extension(" .txt "), ".txt")

    def test_normalize_extension_empty_string(self):
        self.assertEqual(normalize_extension(""), "")

    def test_normalize_extensions_drops_empty(self):
        result = normalize_extensions(["", "  ", ".py"])
        self.assertEqual(result, frozenset({".py"}))


if __name__ == "__main__":
    unittest.main()
