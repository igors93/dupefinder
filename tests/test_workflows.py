"""Workflow YAML validation tests."""

from __future__ import annotations

import unittest
from pathlib import Path

try:
    import yaml  # type: ignore[import-untyped]

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

WORKFLOWS_DIR = Path(__file__).parent.parent / ".github" / "workflows"
CI_YML = WORKFLOWS_DIR / "ci.yml"
PUBLISH_YML = WORKFLOWS_DIR / "publish.yml"


@unittest.skipUnless(YAML_AVAILABLE, "pyyaml not installed — add it to dev dependencies")
class WorkflowYAMLTests(unittest.TestCase):
    def _load(self, path: Path) -> object:
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)

    def test_ci_yml_is_valid_yaml(self) -> None:
        self.assertIsNotNone(self._load(CI_YML))

    def test_publish_yml_is_valid_yaml(self) -> None:
        self.assertIsNotNone(self._load(PUBLISH_YML))

    def test_ci_yml_has_no_markdown_fences(self) -> None:
        content = CI_YML.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            self.assertFalse(
                line.strip().startswith("```"),
                f"Markdown fence found in ci.yml at line {i}: {line!r}",
            )

    def test_publish_yml_has_no_markdown_fences(self) -> None:
        content = PUBLISH_YML.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            self.assertFalse(
                line.strip().startswith("```"),
                f"Markdown fence found in publish.yml at line {i}: {line!r}",
            )

    def test_ci_yml_has_required_jobs(self) -> None:
        data = self._load(CI_YML)
        assert isinstance(data, dict)
        jobs = data.get("jobs", {})
        self.assertIn("quality", jobs, "CI workflow is missing 'quality' job")
        self.assertIn("tests", jobs, "CI workflow is missing 'tests' job")
        self.assertIn("package", jobs, "CI workflow is missing 'package' job")

    def test_publish_yml_has_required_jobs(self) -> None:
        data = self._load(PUBLISH_YML)
        assert isinstance(data, dict)
        jobs = data.get("jobs", {})
        self.assertIn("build", jobs, "Publish workflow is missing 'build' job")
        self.assertIn("publish", jobs, "Publish workflow is missing 'publish' job")

    def test_publish_yml_triggers_on_release(self) -> None:
        data = self._load(PUBLISH_YML)
        assert isinstance(data, dict)
        # PyYAML parses 'on' as the boolean True (YAML 1.1 behaviour).
        on = data.get(True, {})
        self.assertIn("release", on, "Publish workflow should trigger on 'release'")

    def test_ci_yml_triggers_on_push_and_pr(self) -> None:
        data = self._load(CI_YML)
        assert isinstance(data, dict)
        # PyYAML parses 'on' as the boolean True (YAML 1.1 behaviour).
        on = data.get(True, {})
        self.assertIn("push", on, "CI workflow should trigger on 'push'")
        self.assertIn("pull_request", on, "CI workflow should trigger on 'pull_request'")


if __name__ == "__main__":
    unittest.main()
