import tempfile
import unittest
from pathlib import Path

from dupefinder.errors import InvalidOptionError, InvalidPathError, UnsupportedHashAlgorithmError
from dupefinder.models import ScanOptions
from dupefinder.safety import normalize_extensions, validate_options, validate_scan_path


class SafetyTests(unittest.TestCase):
    def test_validate_scan_path_rejects_missing_path(self):
        with self.assertRaises(InvalidPathError):
            validate_scan_path("/path/that/should/not/exist/dupefinder")

    def test_validate_scan_path_accepts_existing_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertEqual(validate_scan_path(temp_dir), Path(temp_dir).resolve())

    def test_validate_options_rejects_invalid_algorithm(self):
        with self.assertRaises(UnsupportedHashAlgorithmError):
            validate_options(ScanOptions(algorithm="fake-hash"))

    def test_validate_options_rejects_bad_chunk_size(self):
        with self.assertRaises(InvalidOptionError):
            validate_options(ScanOptions(chunk_size=0))

    def test_normalize_extensions(self):
        self.assertEqual(normalize_extensions(["jpg", ".PNG", " txt "]), frozenset({".jpg", ".png", ".txt"}))


if __name__ == "__main__":
    unittest.main()
