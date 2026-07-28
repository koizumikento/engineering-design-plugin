"""Tests for the STR-229 unified build123d production route."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
RUNNER = REPO_ROOT / "scripts" / "cad_runner.py"
INSPECT = REPO_ROOT / "scripts" / "cad_inspect.py"
EXAMPLE = (
    REPO_ROOT
    / "examples"
    / "build123d-enclosure-assembly"
    / "src"
    / "enclosure_assembly.py"
)
PRODUCTION_MODELS = [
    REPO_ROOT / "examples" / "calibration-block" / "src" / "calibration_block.py",
    EXAMPLE,
    REPO_ROOT / "examples" / "sensor-enclosure" / "src" / "enclosure.py",
    REPO_ROOT / "examples" / "iot-device" / "src" / "enclosure.py",
    REPO_ROOT / "examples" / "battery-stand" / "src" / "battery_stand.py",
    REPO_ROOT / "templates" / "mechanical" / "box_with_holes.py",
    REPO_ROOT / "templates" / "mechanical" / "bracket.py",
    REPO_ROOT / "templates" / "mechanical" / "enclosure_with_pcb.py",
    REPO_ROOT / "templates" / "mechanical" / "shaft.py",
]


class Build123dProductionTests(unittest.TestCase):
    def test_committed_runtime_and_contract_exist(self) -> None:
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('"build123d==0.11.1"', pyproject)
        self.assertNotIn('"cadquery>=', pyproject)
        self.assertTrue((REPO_ROOT / "uv.lock").is_file())
        self.assertTrue(RUNNER.is_file())
        self.assertTrue(INSPECT.is_file())
        self.assertTrue(EXAMPLE.is_file())
        self.assertFalse((REPO_ROOT / "scripts" / "cadquery_runner.py").exists())
        runner_source = RUNNER.read_text(encoding="utf-8")
        self.assertIn('"build123d_occt"', runner_source)
        self.assertNotIn("cadquery" + "-ocp", runner_source)

        source = EXAMPLE.read_text(encoding="utf-8")
        self.assertIn("RigidJoint", source)
        self.assertIn("cad_expectations", source)
        self.assertIn('label="enclosure_assembly"', source)

    def test_production_python_has_no_cadquery_imports(self) -> None:
        production_roots = [
            REPO_ROOT / "scripts",
            REPO_ROOT / "skills" / "mechanical-cad",
            REPO_ROOT / "templates" / "mechanical",
            REPO_ROOT / "examples",
        ]
        offenders = []
        for root in production_roots:
            for path in root.rglob("*.py"):
                if "__pycache__" in path.parts:
                    continue
                source = path.read_text(encoding="utf-8")
                if "import cadquery" in source or "from cadquery" in source:
                    offenders.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(offenders, [])

    @unittest.skipUnless(
        RUNTIME_PYTHON.is_file(),
        "root build123d runtime is not synced",
    )
    def test_example_exports_and_reimports_with_expected_placement(self) -> None:
        with tempfile.TemporaryDirectory(prefix="str232-build123d-") as directory:
            output = Path(directory)
            subprocess.run(
                [
                    str(RUNTIME_PYTHON),
                    str(RUNNER),
                    str(EXAMPLE),
                    "-o",
                    str(output),
                    "--report",
                    "--fail-on-check",
                ],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            report = json.loads(
                (output / "reports" / "enclosure_assembly-cad-summary.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(report["engine"], "build123d")
            self.assertEqual(
                set(report["runtime"]),
                {"python", "build123d", "build123d_occt"},
            )
            self.assertRegex(report["runtime"]["build123d_occt"], r"^7\.")
            self.assertTrue(report["validation"]["valid"])
            self.assertTrue(report["step_reimport"]["valid"])
            self.assertEqual(
                len(report["step_artifact"]["sha256"]),
                64,
            )
            self.assertEqual(report["step_reimport"]["topology"]["solids"], 2)
            self.assertTrue(report["expectations"]["passed"])
            self.assertEqual(
                [item["label"] for item in report["step_reimport"]["components"]],
                ["base", "lid"],
            )
            source_components = {
                item["label"]: item for item in report["validation"]["components"]
            }
            self.assertEqual(source_components["base"]["joints"], ["lid_seat"])
            self.assertEqual(source_components["lid"]["joints"], ["underside"])

            inspected = subprocess.run(
                [
                    str(RUNTIME_PYTHON),
                    str(INSPECT),
                    "refs",
                    str(output / "enclosure_assembly.step"),
                ],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            inspection = json.loads(inspected.stdout)
            provenance = inspection["artifact"]["related_runner_report"]
            self.assertTrue(provenance["matches"]["source_sha256"])
            self.assertTrue(provenance["matches"]["step_sha256"])
            self.assertTrue(provenance["matches"]["runtime"])
            self.assertTrue(provenance["matches"]["units"])

    @unittest.skipUnless(
        RUNTIME_PYTHON.is_file(),
        "root build123d runtime is not synced",
    )
    def test_all_production_models_export_and_reimport(self) -> None:
        for model in PRODUCTION_MODELS:
            with self.subTest(model=model.relative_to(REPO_ROOT)):
                with tempfile.TemporaryDirectory(
                    prefix="str229-build123d-"
                ) as directory:
                    completed = subprocess.run(
                        [
                            str(RUNTIME_PYTHON),
                            str(RUNNER),
                            str(model),
                            "-o",
                            directory,
                            "--report",
                            "--fail-on-check",
                        ],
                        cwd=REPO_ROOT,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    report = json.loads(completed.stdout)
                    self.assertTrue(report["validation"]["valid"])
                    self.assertTrue(report["step_reimport"]["valid"])
                    self.assertTrue(report["expectations"]["passed"])

    @unittest.skipUnless(
        RUNTIME_PYTHON.is_file(),
        "root build123d runtime is not synced",
    )
    def test_step_preview_smoke(self) -> None:
        with tempfile.TemporaryDirectory(prefix="str229-preview-") as directory:
            output = Path(directory)
            subprocess.run(
                [
                    str(RUNTIME_PYTHON),
                    str(RUNNER),
                    str(PRODUCTION_MODELS[0]),
                    "-o",
                    str(output),
                    "--fail-on-check",
                ],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            env = dict(os.environ)
            env["MPLBACKEND"] = "Agg"
            subprocess.run(
                [
                    str(RUNTIME_PYTHON),
                    str(REPO_ROOT / "scripts" / "preview_generator.py"),
                    str(output / "calibration_block.step"),
                    "-o",
                    str(output / "previews"),
                    "--view",
                    "iso",
                ],
                cwd=REPO_ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertTrue(
                (output / "previews" / "calibration_block-preview.png").is_file()
            )


if __name__ == "__main__":
    unittest.main()
