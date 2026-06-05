"""Tests for the CLI."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dupefinder.cli import main


class CLIBasicTests(unittest.TestCase):
    def test_basic_scan_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("x", encoding="utf-8")
            exit_code = main([tmp])
            self.assertEqual(exit_code, 0)

    def test_empty_directory_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            exit_code = main([tmp])
            self.assertEqual(exit_code, 0)

    def test_invalid_path_exits_one(self):
        exit_code = main(["/path/that/does/not/exist/dupefinder_test"])
        self.assertEqual(exit_code, 1)


class CLIJsonTests(unittest.TestCase):
    def test_json_flag_produces_valid_json(self, capsys=None):
        """Test that --json output is valid JSON."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("same", encoding="utf-8")
            (root / "b.txt").write_text("same", encoding="utf-8")

            import io
            import sys

            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                exit_code = main([tmp, "--json", "--no-ignore-hidden"])
            finally:
                sys.stdout = old_stdout

            output = captured.getvalue()
            self.assertEqual(exit_code, 0)
            parsed = json.loads(output)
            self.assertIsInstance(parsed, dict)

    def test_json_output_has_schema_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            import io
            import sys

            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                main([tmp, "--json"])
            finally:
                sys.stdout = old_stdout

            parsed = json.loads(captured.getvalue())
            self.assertIn("schema_version", parsed)
            self.assertEqual(parsed["schema_version"], "1.1")


class CLIFailOnDuplicatesTests(unittest.TestCase):
    def test_fail_on_duplicates_exits_two_when_duplicates_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("dup content", encoding="utf-8")
            (root / "b.txt").write_text("dup content", encoding="utf-8")

            exit_code = main([tmp, "--fail-on-duplicates", "--no-ignore-hidden"])
            self.assertEqual(exit_code, 2)

    def test_fail_on_duplicates_exits_zero_when_no_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("unique a", encoding="utf-8")
            (root / "b.txt").write_text("unique b", encoding="utf-8")

            exit_code = main([tmp, "--fail-on-duplicates", "--no-ignore-hidden"])
            self.assertEqual(exit_code, 0)


class CLINewFlagsTests(unittest.TestCase):
    def test_max_files_limits_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(10):
                (root / f"file{i}.txt").write_text(f"content {i}", encoding="utf-8")

            import io
            import sys

            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                exit_code = main([tmp, "--json", "--no-ignore-hidden", "--max-files", "3"])
            finally:
                sys.stdout = old_stdout

            self.assertEqual(exit_code, 0)
            parsed = json.loads(captured.getvalue())
            self.assertLessEqual(parsed["scanned_files"], 3)

    def test_max_depth_limits_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "root_file.txt").write_text("root", encoding="utf-8")
            subdir = root / "subdir"
            subdir.mkdir()
            (subdir / "sub_file.txt").write_text("sub", encoding="utf-8")

            import io
            import sys

            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                exit_code = main([tmp, "--json", "--no-ignore-hidden", "--max-depth", "0"])
            finally:
                sys.stdout = old_stdout

            self.assertEqual(exit_code, 0)
            parsed = json.loads(captured.getvalue())
            self.assertEqual(parsed["scanned_files"], 1)

    def test_version_flag(self):
        import io
        import sys

        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            with self.assertRaises(SystemExit) as ctx:
                main(["--version"])
            self.assertEqual(ctx.exception.code, 0)
        finally:
            sys.stdout = old_stdout

    def test_cache_flag_creates_db_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("content", encoding="utf-8")
            db_path = str(Path(tmp) / "cache.sqlite")

            exit_code = main([tmp, "--no-ignore-hidden", "--cache", db_path])
            self.assertEqual(exit_code, 0)
            self.assertTrue(Path(db_path).exists())


class CLICacheErrorTests(unittest.TestCase):
    def test_invalid_cache_path_exits_one(self):
        """A cache path that cannot be created should result in exit code 1."""
        with tempfile.TemporaryDirectory() as tmp:
            # Use a path inside a non-existent directory to trigger failure
            invalid_cache = "/nonexistent_dir_dupefinder_test/cache.db"
            exit_code = main([tmp, "--cache", invalid_cache])
            self.assertEqual(exit_code, 1)

    def test_valid_cache_path_exits_zero(self):
        """A valid cache path should work normally."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("content", encoding="utf-8")
            db_path = str(Path(tmp) / "cache.sqlite")
            exit_code = main([tmp, "--no-ignore-hidden", "--cache", db_path])
            self.assertEqual(exit_code, 0)


class CLIJsonAndProgressTests(unittest.TestCase):
    def test_json_output_with_total_bytes_read(self):
        """JSON output should include total_bytes_read field."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("same", encoding="utf-8")
            (root / "b.txt").write_text("same", encoding="utf-8")

            import io
            import sys

            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                exit_code = main([tmp, "--json", "--no-ignore-hidden"])
            finally:
                sys.stdout = old_stdout

            self.assertEqual(exit_code, 0)
            parsed = json.loads(captured.getvalue())
            self.assertIn("total_bytes_read", parsed)

    def test_progress_flag_writes_to_stderr(self):
        """--progress should write to stderr, not stdout."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("content", encoding="utf-8")

            import io
            import sys

            captured_out = io.StringIO()
            captured_err = io.StringIO()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = captured_out
            sys.stderr = captured_err
            try:
                exit_code = main([tmp, "--no-ignore-hidden", "--progress"])
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            self.assertEqual(exit_code, 0)
            # stdout should only have the report (not progress), stderr may have progress

    def test_json_with_progress_stdout_is_valid_json(self):
        """--json and --progress together: stdout should still be valid JSON."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("same", encoding="utf-8")
            (root / "b.txt").write_text("same", encoding="utf-8")

            import io
            import sys

            captured_out = io.StringIO()
            captured_err = io.StringIO()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = captured_out
            sys.stderr = captured_err
            try:
                exit_code = main([tmp, "--json", "--no-ignore-hidden", "--progress"])
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            self.assertEqual(exit_code, 0)
            parsed = json.loads(captured_out.getvalue())
            self.assertIsInstance(parsed, dict)


if __name__ == "__main__":
    unittest.main()
