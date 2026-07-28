"""Structural tests for the STR-231 agent-generation benchmark."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = REPO_ROOT / "pocs" / "build123d-migration" / "benchmark"
POC_PYTHON = BENCHMARK_ROOT.parent / ".venv" / "bin" / "python"
sys.path.insert(0, str(BENCHMARK_ROOT / "scripts"))

from benchmark_common import validate_manifest  # noqa: E402


class Str231BenchmarkTest(unittest.TestCase):
    def test_manifest_declares_complete_sixty_trial_matrix(self) -> None:
        manifest = json.loads(
            (BENCHMARK_ROOT / "manifest.json").read_text(encoding="utf-8")
        )
        validation = validate_manifest(manifest)
        self.assertEqual(validation["spec_count"], 10)
        self.assertEqual(validation["expected_trial_count"], 60)

    def test_all_first_submission_sources_exist_and_are_unique(self) -> None:
        sources = []
        for engine in ("cadquery", "build123d"):
            for spec_dir in sorted((BENCHMARK_ROOT / "trials" / engine).iterdir()):
                for trial in range(1, 4):
                    source = spec_dir / f"trial-{trial}.py"
                    self.assertTrue(source.is_file(), source)
                    sources.append(source)
        self.assertEqual(len(sources), 60)
        hashes = {
            hashlib.sha256(source.read_bytes()).hexdigest()
            for source in sources
        }
        self.assertEqual(len(hashes), 60)

    def test_published_result_is_complete_and_gate_is_not_met(self) -> None:
        result = json.loads(
            (BENCHMARK_ROOT / "results" / "summary.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(result["trial_count"], 60)
        self.assertFalse(result["migration_gate"]["passed"])
        for engine in ("cadquery", "build123d"):
            summary = result["summary"]["by_engine"][engine]
            self.assertEqual(summary["first_run_execution_rate"], 1.0)
            self.assertEqual(summary["full_spec_pass_rate"], 1.0)

    @unittest.skipUnless(POC_PYTHON.exists(), "build123d PoC environment missing")
    def test_trimmed_cylinder_radius_is_inspectable(self) -> None:
        code = f"""
import sys
sys.path.insert(0, {str(BENCHMARK_ROOT / 'scripts')!r})
from build123d import Align, Box, Cylinder, GeomType, Pos
from inspect_step import cylinder_radius
blank = Box(30, 20, 4, align=(Align.CENTER, Align.CENTER, Align.MIN))
tool = Box(14, 6, 4, align=(Align.CENTER, Align.CENTER, Align.MIN))
tool += Pos(-7, 0, 0) * Cylinder(
    3, 4, align=(Align.CENTER, Align.CENTER, Align.MIN)
)
tool += Pos(7, 0, 0) * Cylinder(
    3, 4, align=(Align.CENTER, Align.CENTER, Align.MIN)
)
shape = blank - tool
radii = [
    cylinder_radius(face)
    for face in shape.faces()
    if face.geom_type == GeomType.CYLINDER
]
assert radii == [3.0, 3.0], radii
"""
        result = subprocess.run(
            [str(POC_PYTHON), "-c", code],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
