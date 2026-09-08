"""Tests for the repository-local plugin release gate."""

from __future__ import annotations

import subprocess
import json
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.validate_release import validate_evals


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "scripts" / "validate_release.py"


class ReleaseValidationTests(unittest.TestCase):
    def test_eval_validation_rejects_unverifiable_and_duplicate_cases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "integration"
            (skill / "evals").mkdir(parents=True)
            case = {"id": "same", "prompt": "check fit", "expected_output": "measured fit", "assertions": [], "files": ["../outside.step"]}
            (skill / "evals/evals.json").write_text(json.dumps({"skill_name": skill.name, "evals": [case, case]}), encoding="utf-8")
            errors = []
            validate_evals(skill, errors)
            self.assertTrue(any("assertions" in error for error in errors))
            self.assertTrue(any("duplicate" in error for error in errors))
            self.assertTrue(any("input file" in error for error in errors))

    def test_release_gate_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            completed.returncode,
            0,
            msg=f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )
        self.assertIn("4 skills", completed.stdout)
        self.assertIn("plugin 2.2.0", completed.stdout)

    def test_ci_has_read_only_permissions_and_frozen_sync(self) -> None:
        workflow = (
            REPO_ROOT / ".github" / "workflows" / "ci.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertNotIn(": write", workflow)
        self.assertIn("uv sync --frozen", workflow)
        self.assertIn("MPLBACKEND: Agg", workflow)


if __name__ == "__main__":
    unittest.main()
