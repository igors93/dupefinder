"""Packaging integrity tests."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


def _read_pyproject_version() -> str:
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")
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
        src = Path(__file__).parent.parent / "src" / "dupefinder" / "py.typed"
        self.assertTrue(src.exists(), f"py.typed not found at {src}")

    def test_py_typed_is_empty(self) -> None:
        src = Path(__file__).parent.parent / "src" / "dupefinder" / "py.typed"
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

    def test_python_version_meets_minimum(self) -> None:
        self.assertGreaterEqual(
            sys.version_info[:2],
            (3, 10),
            "dupefinder requires Python 3.10 or later",
        )


if __name__ == "__main__":
    unittest.main()
