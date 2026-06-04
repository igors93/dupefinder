import tempfile
import unittest
from pathlib import Path

from dupefinder.errors import UnsupportedHashAlgorithmError
from dupefinder.hashing import hash_file


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


if __name__ == "__main__":
    unittest.main()
