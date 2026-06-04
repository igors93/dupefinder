import tempfile
import unittest
from pathlib import Path

from dupefinder.errors import FileHashError, UnsupportedHashAlgorithmError
from dupefinder.hashing import hash_file, hash_files
from dupefinder.models import FileInfo, ScanOptions


class HashingTests(unittest.TestCase):
    def test_equal_files_have_equal_hashes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "a.txt"
            second = root / "b.txt"
            first.write_text("same content", encoding="utf-8")
            second.write_text("same content", encoding="utf-8")

            self.assertEqual(hash_file(first), hash_file(second))

    def test_different_files_have_different_hashes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "a.txt"
            second = root / "b.txt"
            first.write_text("one", encoding="utf-8")
            second.write_text("two", encoding="utf-8")

            self.assertNotEqual(hash_file(first), hash_file(second))

    def test_invalid_algorithm_raises_clear_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "a.txt"
            file_path.write_text("data", encoding="utf-8")

            with self.assertRaises(UnsupportedHashAlgorithmError):
                hash_file(file_path, algorithm="not-a-real-algorithm")

    def test_chunk_size_zero_raises(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "a.txt"
            file_path.write_text("data", encoding="utf-8")

            with self.assertRaises(ValueError):
                hash_file(file_path, chunk_size=0)

    def test_hash_file_accepts_string_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "a.txt"
            file_path.write_text("hello", encoding="utf-8")

            result = hash_file(str(file_path))
            self.assertIsInstance(result, str)
            self.assertTrue(len(result) > 0)

    def test_hash_file_alternative_algorithm(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "a.txt"
            file_path.write_text("hello", encoding="utf-8")

            sha256 = hash_file(file_path, algorithm="sha256")
            md5 = hash_file(file_path, algorithm="md5")

            self.assertNotEqual(sha256, md5)

    def test_hash_files_skips_on_error_by_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            good = root / "good.txt"
            good.write_text("data", encoding="utf-8")
            missing = root / "missing.txt"

            options = ScanOptions(on_error="skip")
            files = [
                FileInfo(path=good, size=4),
                FileInfo(path=missing, size=0),
            ]
            issues: list = []
            results = list(hash_files(files, options, issues))

            self.assertEqual(len(results), 1)
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0].phase, "hash")

    def test_hash_files_raises_in_strict_mode(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing.txt"
            options = ScanOptions(on_error="raise")
            files = [FileInfo(path=missing, size=0)]

            with self.assertRaises(FileHashError):
                list(hash_files(files, options))


if __name__ == "__main__":
    unittest.main()
