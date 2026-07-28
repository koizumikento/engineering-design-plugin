#!/usr/bin/env python3
"""Run the complete STR-228 migration PoC from the repository root."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


POC_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = POC_ROOT.parents[1]
MANIFEST = POC_ROOT / "manifest.json"
ROOT_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
POC_PYTHON = POC_ROOT / ".venv" / "bin" / "python"


def run_command(
    command: list[str],
    *,
    cwd: Path = REPO_ROOT,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def require_environments() -> None:
    missing = [path for path in (ROOT_PYTHON, POC_PYTHON) if not path.exists()]
    if missing:
        raise RuntimeError(
            "missing Python environment(s): "
            + ", ".join(str(path) for path in missing)
            + "\nRun `uv sync` and `uv sync --project pocs/build123d-migration`."
        )


def prepare_output(output_root: Path) -> None:
    output_root = output_root.resolve()
    expected_parent = (REPO_ROOT / "outputs").resolve()
    if expected_parent not in output_root.parents:
        raise ValueError(f"output must be below {expected_parent}: {output_root}")
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)


def capture_legacy(manifest: dict, output_root: Path) -> None:
    summaries = {}
    for name, relative_source in manifest["legacy_sources"].items():
        print(f"[legacy] {name}", flush=True)
        source = (REPO_ROOT / relative_source).resolve()
        work = output_root / "legacy" / name / "work"
        generated = output_root / "legacy" / name / "generated"
        (work / "outputs").mkdir(parents=True, exist_ok=True)
        generated.mkdir(parents=True, exist_ok=True)
        result = run_command(
            [
                str(ROOT_PYTHON),
                str(REPO_ROOT / "scripts" / "cadquery_runner.py"),
                str(source),
                "-o",
                str(generated),
                "--name",
                name,
                "--format",
                "step",
                "--report",
                "--fail-on-invalid",
            ],
            cwd=work,
            check=False,
        )
        summaries[name] = {
            "source": str(source),
            "returncode": result.returncode,
            "passed": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    summary_path = output_root / "legacy" / "summary.json"
    summary_path.write_text(
        json.dumps(summaries, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def generate_models(
    manifest: dict,
    output_root: Path,
    *,
    previews: bool,
) -> tuple[dict, dict]:
    timings: dict[str, dict[str, float]] = {}
    repeatability: dict[str, dict[str, bool]] = {}
    for name, config in manifest["models"].items():
        print(f"[generate] {name}", flush=True)
        timings[name] = {}
        repeatability[name] = {}
        cadquery_output = output_root / "generated" / "cadquery" / name
        build123d_output = output_root / "generated" / "build123d" / name
        cadquery_output.mkdir(parents=True, exist_ok=True)
        build123d_output.mkdir(parents=True, exist_ok=True)

        started = time.perf_counter()
        run_command(
            [
                str(ROOT_PYTHON),
                str(REPO_ROOT / "scripts" / "cadquery_runner.py"),
                str(POC_ROOT / config["cadquery_source"]),
                "-o",
                str(cadquery_output),
                "--name",
                name,
                "--format",
                "step,stl",
                "--report",
                "--fail-on-invalid",
            ]
        )
        timings[name]["cadquery_generation_seconds"] = round(
            time.perf_counter() - started,
            6,
        )
        started = time.perf_counter()
        run_command(
            [
                str(POC_PYTHON),
                str(POC_ROOT / "scripts" / "build123d_runner.py"),
                str(POC_ROOT / config["build123d_source"]),
                "-o",
                str(build123d_output),
                "--name",
                name,
            ]
        )
        timings[name]["build123d_generation_seconds"] = round(
            time.perf_counter() - started,
            6,
        )

        for engine, generated in (
            ("cadquery", cadquery_output),
            ("build123d", build123d_output),
        ):
            print(f"[inspect] {engine}/{name}", flush=True)
            step_path = generated / f"{name}.step"
            inspection_path = output_root / "inspections" / engine / f"{name}.json"
            run_command(
                [
                    str(POC_PYTHON),
                    str(POC_ROOT / "scripts" / "inspect_step.py"),
                    str(step_path),
                    "-o",
                    str(inspection_path),
                ]
            )
            if previews:
                print(f"[preview] {engine}/{name}", flush=True)
                preview_output = output_root / "previews" / engine / name
                run_command(
                    [
                        str(ROOT_PYTHON),
                        str(REPO_ROOT / "scripts" / "preview_generator.py"),
                        str(step_path),
                        "-o",
                        str(preview_output),
                        "--all-views",
                    ]
                )

        for engine, source_key, python, runner in (
            (
                "cadquery",
                "cadquery_source",
                ROOT_PYTHON,
                REPO_ROOT / "scripts" / "cadquery_runner.py",
            ),
            (
                "build123d",
                "build123d_source",
                POC_PYTHON,
                POC_ROOT / "scripts" / "build123d_runner.py",
            ),
        ):
            print(f"[repeat] {engine}/{name}", flush=True)
            repeat_output = output_root / "generated-repeat" / engine / name
            repeat_output.mkdir(parents=True, exist_ok=True)
            command = [
                str(python),
                str(runner),
                str(POC_ROOT / config[source_key]),
                "-o",
                str(repeat_output),
                "--name",
                name,
            ]
            if engine == "cadquery":
                command.extend(
                    [
                        "--format",
                        "step",
                        "--report",
                        "--fail-on-invalid",
                    ]
                )
            run_command(command)
            repeat_inspection = (
                output_root / "inspections-repeat" / engine / f"{name}.json"
            )
            run_command(
                [
                    str(POC_PYTHON),
                    str(POC_ROOT / "scripts" / "inspect_step.py"),
                    str(repeat_output / f"{name}.step"),
                    "-o",
                    str(repeat_inspection),
                ]
            )
            primary = json.loads(
                (
                    output_root / "inspections" / engine / f"{name}.json"
                ).read_text(encoding="utf-8")
            )
            repeated = json.loads(repeat_inspection.read_text(encoding="utf-8"))
            comparable_keys = (
                "valid",
                "bbox_mm",
                "volume_mm3",
                "area_mm2",
                "center_of_mass_mm",
                "topology",
                "cylinders",
            )
            repeatability[name][engine] = all(
                primary[key] == repeated[key] for key in comparable_keys
            )
    return timings, repeatability


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "outputs" / "build123d-migration-poc",
    )
    parser.add_argument("--skip-previews", action="store_true")
    parser.add_argument("--skip-legacy", action="store_true")
    args = parser.parse_args()

    require_environments()
    output_root = args.output.resolve()
    prepare_output(output_root)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not args.skip_legacy:
        capture_legacy(manifest, output_root)
    timings, repeatability = generate_models(
        manifest,
        output_root,
        previews=not args.skip_previews,
    )
    (output_root / "timings.json").write_text(
        json.dumps(timings, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_root / "repeatability.json").write_text(
        json.dumps(repeatability, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if not all(
        passed
        for engines in repeatability.values()
        for passed in engines.values()
    ):
        raise RuntimeError("repeatability check failed")

    comparison = run_command(
        [
            str(POC_PYTHON),
            str(POC_ROOT / "scripts" / "compare.py"),
            "--manifest",
            str(MANIFEST),
            "--output-root",
            str(output_root),
        ],
        check=False,
    )
    print(comparison.stdout)
    if comparison.stderr:
        print(comparison.stderr, file=sys.stderr)
    return comparison.returncode


if __name__ == "__main__":
    raise SystemExit(main())
