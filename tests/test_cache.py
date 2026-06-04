"""Tests for SQLiteHashCache."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dupefinder.cache import HashCache, SQLiteHashCache


class SQLiteHashCacheTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmpdir.name) / "test_cache.sqlite"
        self.cache = SQLiteHashCache(self.db_path)
        # Fake path for testing
        self.fake_path = Path("/some/file.txt")

    def tearDown(self):
        try:
            self.cache.close()
        except Exception:
            pass
        self._tmpdir.cleanup()

    def test_cache_miss_returns_none(self):
        result = self.cache.get(
            self.fake_path,
            size=100,
            mtime_ns=123456789,
            algorithm="sha256",
        )
        self.assertIsNone(result)

    def test_set_and_get_round_trip(self):
        self.cache.set(
            self.fake_path,
            size=100,
            mtime_ns=123456789,
            algorithm="sha256",
            digest="abc123",
        )
        result = self.cache.get(
            self.fake_path,
            size=100,
            mtime_ns=123456789,
            algorithm="sha256",
        )
        self.assertEqual(result, "abc123")

    def test_stale_entry_size_changed_returns_none(self):
        self.cache.set(
            self.fake_path,
            size=100,
            mtime_ns=123456789,
            algorithm="sha256",
            digest="abc123",
        )
        # Different size
        result = self.cache.get(
            self.fake_path,
            size=200,
            mtime_ns=123456789,
            algorithm="sha256",
        )
        self.assertIsNone(result)

    def test_stale_entry_mtime_changed_returns_none(self):
        self.cache.set(
            self.fake_path,
            size=100,
            mtime_ns=123456789,
            algorithm="sha256",
            digest="abc123",
        )
        # Different mtime_ns
        result = self.cache.get(
            self.fake_path,
            size=100,
            mtime_ns=999999999,
            algorithm="sha256",
        )
        self.assertIsNone(result)

    def test_different_algorithms_are_independent(self):
        self.cache.set(
            self.fake_path,
            size=100,
            mtime_ns=123456789,
            algorithm="sha256",
            digest="sha256digest",
        )
        self.cache.set(
            self.fake_path,
            size=100,
            mtime_ns=123456789,
            algorithm="md5",
            digest="md5digest",
        )
        result_sha256 = self.cache.get(
            self.fake_path, size=100, mtime_ns=123456789, algorithm="sha256"
        )
        result_md5 = self.cache.get(
            self.fake_path, size=100, mtime_ns=123456789, algorithm="md5"
        )
        self.assertEqual(result_sha256, "sha256digest")
        self.assertEqual(result_md5, "md5digest")

    def test_update_overwrites_existing_entry(self):
        self.cache.set(
            self.fake_path,
            size=100,
            mtime_ns=123456789,
            algorithm="sha256",
            digest="old_digest",
        )
        self.cache.set(
            self.fake_path,
            size=100,
            mtime_ns=999999999,
            algorithm="sha256",
            digest="new_digest",
        )
        result = self.cache.get(
            self.fake_path,
            size=100,
            mtime_ns=999999999,
            algorithm="sha256",
        )
        self.assertEqual(result, "new_digest")

    def test_context_manager_closes_connection(self):
        db_path = Path(self._tmpdir.name) / "ctx_test.sqlite"
        with SQLiteHashCache(db_path) as cache:
            cache.set(
                self.fake_path,
                size=50,
                mtime_ns=1,
                algorithm="sha256",
                digest="ctx_digest",
            )
        # After context exit, connection should be closed
        # Verify by opening a new connection and reading
        with SQLiteHashCache(db_path) as cache2:
            result = cache2.get(
                self.fake_path, size=50, mtime_ns=1, algorithm="sha256"
            )
        self.assertEqual(result, "ctx_digest")

    def test_close_can_be_called_directly(self):
        db_path = Path(self._tmpdir.name) / "close_test.sqlite"
        cache = SQLiteHashCache(db_path)
        cache.close()  # Should not raise

    def test_persists_across_instances(self):
        """Data written in one instance should be readable in a new instance."""
        self.cache.set(
            self.fake_path,
            size=42,
            mtime_ns=555,
            algorithm="sha256",
            digest="persistent",
        )
        self.cache.close()

        cache2 = SQLiteHashCache(self.db_path)
        try:
            result = cache2.get(self.fake_path, size=42, mtime_ns=555, algorithm="sha256")
            self.assertEqual(result, "persistent")
        finally:
            cache2.close()


class HashCacheProtocolTests(unittest.TestCase):
    def test_sqlite_cache_implements_protocol(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "proto_test.sqlite"
            cache = SQLiteHashCache(db_path)
            try:
                self.assertIsInstance(cache, HashCache)
            finally:
                cache.close()


if __name__ == "__main__":
    unittest.main()
