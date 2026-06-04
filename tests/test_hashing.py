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


class HashFileCancellationTests(unittest.TestCase):
    def test_should_cancel_raises_scan_cancelled(self):
        """hash_file with should_cancel=True raises _ScanCancelled."""
        from dupefinder.errors import _ScanCancelled

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "a.txt"
            file_path.write_bytes(b"x" * 100)

            with self.assertRaises(_ScanCancelled):
                hash_file(file_path, chunk_size=1, should_cancel=lambda: True)

    def test_should_cancel_not_called_for_empty_file(self):
        """Empty file produces no chunks, so should_cancel is never called."""
        from dupefinder.errors import _ScanCancelled

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "empty.txt"
            file_path.write_bytes(b"")

            # Should not raise — no chunks to read
            result = hash_file(file_path, should_cancel=lambda: True)
            self.assertIsInstance(result, str)

    def test_on_bytes_read_callback_receives_correct_count(self):
        """on_bytes_read should be called with the number of bytes per chunk."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "a.txt"
            file_path.write_bytes(b"x" * 100)

            bytes_seen = []
            hash_file(file_path, chunk_size=10, on_bytes_read=bytes_seen.append)

            self.assertEqual(sum(bytes_seen), 100)
            # Each chunk should be 10 bytes
            self.assertEqual(bytes_seen, [10] * 10)

    def test_on_bytes_read_total_equals_file_size(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "data.bin"
            file_path.write_bytes(b"abc" * 50)

            total = [0]
            hash_file(file_path, on_bytes_read=lambda n: total.__setitem__(0, total[0] + n))

            self.assertEqual(total[0], 150)

    def test_hash_files_passes_on_bytes_read_to_file(self):
        """hash_files should accumulate bytes read across all files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "a.txt").write_bytes(b"x" * 50)
            (root / "b.txt").write_bytes(b"x" * 50)

            options = ScanOptions(on_error="skip")
            files = [
                FileInfo(path=root / "a.txt", size=50),
                FileInfo(path=root / "b.txt", size=50),
            ]
            total = [0]
            list(hash_files(files, options, on_bytes_read=lambda n: total.__setitem__(0, total[0] + n)))

            self.assertEqual(total[0], 100)


if __name__ == "__main__":
    unittest.main()
