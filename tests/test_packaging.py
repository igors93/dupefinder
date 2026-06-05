"""Packaging integrity tests."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _read_pyproject_version() -> str:
    content = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if match is None:
        raise AssertionError("version not found in pyproject.toml")
    return match.group(1)


class VersionConsistencyTests(unittest.TestCase):
    def test_pyproject_version_matches_init_version(self) -> None:
        import dupefinder

        pyproject_version = _read_pyproject_version()
        self.assertEqual(
            dupefinder.__version__,
            pyproject_version,
            f"dupefinder.__version__ ({dupefinder.__version__!r}) does not match "
            f"pyproject.toml ({pyproject_version!r})",
        )

    def test_version_is_a_string(self) -> None:
        import dupefinder

        self.assertIsInstance(dupefinder.__version__, str)

    def test_version_is_non_empty(self) -> None:
        import dupefinder

        self.assertTrue(dupefinder.__version__)


class PyTypedTests(unittest.TestCase):
    def test_py_typed_marker_exists(self) -> None:
        src = ROOT / "src" / "dupefinder" / "py.typed"
        self.assertTrue(src.exists(), f"py.typed not found at {src}")

    def test_py_typed_is_empty(self) -> None:
        src = ROOT / "src" / "dupefinder" / "py.typed"
        if src.exists():
            self.assertEqual(src.read_text(), "", "py.typed should be an empty marker file")


class CLIEntryPointTests(unittest.TestCase):
    def test_cli_main_is_importable(self) -> None:
        from dupefinder.cli import main

        self.assertTrue(callable(main))

    def test_public_api_is_importable(self) -> None:
        from dupefinder import DupeFinder, ScanOptions, find_duplicates, scan

        self.assertTrue(callable(scan))
        self.assertTrue(callable(find_duplicates))
        self.assertTrue(callable(DupeFinder))
        self.assertTrue(callable(ScanOptions))

    def test_sqlite_hash_cache_importable_from_module(self) -> None:
        from dupefinder.cache import SQLiteHashCache

        self.assertTrue(callable(SQLiteHashCache))

    def test_python_version_meets_minimum(self) -> None:
        self.assertGreaterEqual(
            sys.version_info[:2],
            (3, 10),
            "dupefinder requires Python 3.10 or later",
        )


class READMEDocumentationTests(unittest.TestCase):
    _readme: str = ""

    @classmethod
    def setUpClass(cls) -> None:
        cls._readme = (ROOT / "README.md").read_text(encoding="utf-8")

    def test_readme_documents_exit_code_zero(self) -> None:
        self.assertIn("| `0`", self._readme, "README must document exit code 0")

    def test_readme_documents_exit_code_one(self) -> None:
        self.assertIn("| `1`", self._readme, "README must document exit code 1")

    def test_readme_documents_exit_code_two(self) -> None:
        self.assertIn("| `2`", self._readme, "README must document exit code 2")

    def test_readme_documents_exit_code_three(self) -> None:
        self.assertIn("| `3`", self._readme, "README must document exit code 3")

    def test_readme_notes_exit_code_3_priority(self) -> None:
        self.assertIn(
            "priority",
            self._readme.lower(),
            "README must clarify that exit code 3 takes priority over --fail-on-duplicates",
        )


class ChangelogStructureTests(unittest.TestCase):
    _changelog: str = ""

    @classmethod
    def setUpClass(cls) -> None:
        cls._changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    def test_changelog_has_unreleased_section_first(self) -> None:
        lines = self._changelog.splitlines()
        headers = [line.strip() for line in lines if line.startswith("## ")]
        self.assertTrue(headers, "No ## sections found in CHANGELOG")
        self.assertIn("[Unreleased]", headers[0], "First ## section must be [Unreleased]")

    def test_changelog_current_version_exists(self) -> None:
        import dupefinder

        self.assertIn(
            dupefinder.__version__,
            self._changelog,
            f"CHANGELOG must contain a section for version {dupefinder.__version__}",
        )

    def test_changelog_exit_code_3_not_in_030_section(self) -> None:
        # Exit code 3 was added after v0.3.0; it must not be listed under [0.3.0].
        changelog = self._changelog
        idx_030 = changelog.find("## [0.3.0]")
        idx_010 = changelog.find("## [0.1.0]")
        if idx_030 == -1 or idx_010 == -1:
            return
        section_030 = changelog[idx_030:idx_010]
        self.assertNotIn(
            "exit status `3`",
            section_030,
            "Exit code 3 must not be listed under [0.3.0]; it was introduced later",
        )
        self.assertNotIn(
            "exit code `3`",
            section_030,
            "Exit code 3 must not be listed under [0.3.0]; it was introduced later",
        )


if __name__ == "__main__":
    unittest.main()
