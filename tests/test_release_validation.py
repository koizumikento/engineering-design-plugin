"""Tests for the repository-local plugin release gate."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "scripts" / "validate_release.py"


class ReleaseValidationTests(unittest.TestCase):
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
        self.assertIn("plugin 2.0.0", completed.stdout)

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
