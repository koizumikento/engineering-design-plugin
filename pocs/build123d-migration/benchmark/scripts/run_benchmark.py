#!/usr/bin/env python3
"""Run STR-231 generated CAD trials through neutral, source-blind checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from benchmark_common import (
    ENGINES,
    classify_execution_failure,
    judge_inspection,
    read_json,
    source_metrics,
    specs_map,
    validate_manifest,
    vector3,
    write_json,
)
from report import write_reports


SCRIPT_DIR = Path(__file__).resolve().parent
BENCHMARK_ROOT = SCRIPT_DIR.parent
POC_ROOT = BENCHMARK_ROOT.parent
REPO_ROOT = POC_ROOT.parents[1]
DEFAULT_MANIFEST = BENCHMARK_ROOT / "manifest.json"
DEFAULT_OUTPUT = REPO_ROOT / "outputs" / "str231-agent-benchmark"
ROOT_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
POC_PYTHON = POC_ROOT / ".venv" / "bin" / "python"
CONTRACT_PATH = BENCHMARK_ROOT / "CONTRACT.md"
TASK_TEMPLATE_PATH = BENCHMARK_ROOT / "TRIAL_TASK.md"


def command_for(engine: str, source: Path, output: Path, name: str) -> list[str]:
    if engine == "cadquery":
        return [
            str(ROOT_PYTHON),
            str(REPO_ROOT / "scripts" / "cadquery_runner.py"),
            str(source),
            "-o",
            str(output),
            "--name",
            name,
            "--format",
            "step",
            "--report",
            "--fail-on-invalid",
        ]
    if engine == "build123d":
        return [
            str(POC_PYTHON),
            str(POC_ROOT / "scripts" / "build123d_runner.py"),
            str(source),
            "-o",
            str(output),
            "--name",
            name,
        ]
    raise ValueError(f"unsupported engine: {engine}")


def safe_trial_output(output_root: Path, engine: str, spec: str, trial: int) -> Path:
    resolved_root = output_root.resolve()
    allowed_parent = (REPO_ROOT / "outputs").resolve()
    if resolved_root != allowed_parent and allowed_parent not in resolved_root.parents:
        raise ValueError(f"output root must be below {allowed_parent}")
    trial_output = resolved_root / "trials" / engine / spec / f"trial-{trial}"
    if trial_output.exists():
        shutil.rmtree(trial_output)
    trial_output.mkdir(parents=True)
    return trial_output


def execute(
    command: list[str],
    *,
    timeout_seconds: float,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        process = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
        return {
            "returncode": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr,
            "timed_out": False,
            "wall_time_seconds": round(time.perf_counter() - started, 6),
        }
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else (error.stderr or "")
        return {
            "returncode": None,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": True,
            "wall_time_seconds": round(time.perf_counter() - started, 6),
        }


def inspect_step(
    step_path: Path,
    inspection_path: Path,
    spec: dict[str, Any],
    timeout_seconds: float,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    command = [
        str(POC_PYTHON),
        str(SCRIPT_DIR / "inspect_step.py"),
        str(step_path),
        "-o",
        str(inspection_path),
    ]
    for probe in spec.get("point_probes", []):
        command.extend(
            ["--probe", *(str(value) for value in vector3(probe["point"], "probe"))]
        )
    process = execute(command, timeout_seconds=timeout_seconds)
    inspection = None
    if process["returncode"] in (0, 3) and inspection_path.exists():
        value = read_json(inspection_path)
        if "error" not in value:
            inspection = value
    return inspection, process


def trial_source(engine: str, spec: str, trial: int, repair: int = 0) -> Path:
    stem = f"trial-{trial}" if repair == 0 else f"trial-{trial}-repair-{repair}"
    return BENCHMARK_ROOT / "trials" / engine / spec / f"{stem}.py"


def prompt_provenance(
    engine: str,
    spec_name: str,
    spec: dict[str, Any],
    trial: int,
) -> dict[str, Any]:
    spec_path = BENCHMARK_ROOT / spec["spec_file"]
    guide_path = BENCHMARK_ROOT / "engine-guides" / f"{engine}.md"
    output_path = trial_source(engine, spec_name, trial)
    template = TASK_TEMPLATE_PATH.read_text(encoding="utf-8")
    rendered = (
        template.replace("{SPEC_PATH}", str(spec_path.relative_to(REPO_ROOT)))
        .replace("{ENGINE}", engine)
        .replace("{ENGINE_GUIDE}", str(guide_path.relative_to(REPO_ROOT)))
        .replace("{OUTPUT_PATH}", str(output_path.relative_to(REPO_ROOT)))
    )
    inputs = {
        "contract": CONTRACT_PATH,
        "task_template": TASK_TEMPLATE_PATH,
        "specification": spec_path,
        "engine_guide": guide_path,
    }
    combined = "\n".join(
        [
            CONTRACT_PATH.read_text(encoding="utf-8"),
            rendered,
            spec_path.read_text(encoding="utf-8"),
            guide_path.read_text(encoding="utf-8"),
        ]
    )
    return {
        "sha256": hashlib.sha256(combined.encode("utf-8")).hexdigest(),
        "input_sha256": {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in inputs.items()
        },
        "rendered_task_sha256": hashlib.sha256(
            rendered.encode("utf-8")
        ).hexdigest(),
        "agent": "Codex subagent with inherited model",
        "exact_model_build": None,
        "token_usage": None,
        "not_evaluated": [
            "exact model build identifier is not exposed by the host",
            "per-agent token usage is not exposed by the collaboration API",
            "agent generation wall time is not exposed by the collaboration API",
        ],
    }


def run_trial(
    manifest: dict[str, Any],
    spec_name: str,
    spec: dict[str, Any],
    engine: str,
    trial: int,
    output_root: Path,
    timeout_seconds: float,
    max_repairs: int,
) -> dict[str, Any]:
    output = safe_trial_output(output_root, engine, spec_name, trial)
    first_source = trial_source(engine, spec_name, trial)
    if not first_source.exists():
        raise FileNotFoundError(f"missing trial source: {first_source}")

    attempts: list[dict[str, Any]] = []
    final_judgement: dict[str, Any] | None = None
    final_inspection: dict[str, Any] | None = None
    total_wall = 0.0
    first_execution_pass = False
    first_judgement: dict[str, Any] | None = None
    used_source = first_source

    for repair in range(max_repairs + 1):
        source = trial_source(engine, spec_name, trial, repair)
        if not source.exists():
            break
        used_source = source
        attempt_output = output / f"round-{repair}"
        attempt_output.mkdir(parents=True)
        name = f"{spec_name}-trial-{trial}-round-{repair}"
        generation = execute(
            command_for(engine, source.resolve(), attempt_output, name),
            timeout_seconds=timeout_seconds,
        )
        total_wall += generation["wall_time_seconds"]
        step_path = attempt_output / f"{name}.step"
        execution_pass = generation["returncode"] == 0 and step_path.exists()
        if repair == 0:
            first_execution_pass = execution_pass

        inspection = None
        inspection_process = None
        if step_path.exists():
            inspection_path = attempt_output / "neutral-inspection.json"
            inspection, inspection_process = inspect_step(
                step_path,
                inspection_path,
                spec,
                timeout_seconds,
            )
            total_wall += inspection_process["wall_time_seconds"]

        judgement = judge_inspection(
            manifest,
            spec_name,
            spec,
            inspection,
            execution_pass=execution_pass,
        )
        if repair == 0:
            first_judgement = judgement
        failures = list(judgement["failure_taxonomy"])
        if not execution_pass:
            failures.append(
                classify_execution_failure(
                    generation["stdout"],
                    generation["stderr"],
                    timed_out=generation["timed_out"],
                )
            )
        if step_path.exists() and inspection is None:
            failures.append("step_import_error")
        failures = sorted(set(failures))
        attempt = {
            "round": repair,
            "source_metrics": source_metrics(source),
            "generation": generation,
            "step": str(step_path) if step_path.exists() else None,
            "inspection_process": inspection_process,
            "inspection": inspection,
            "judgement": judgement,
            "failure_taxonomy": failures,
        }
        attempts.append(attempt)
        write_json(attempt_output / "attempt.json", attempt)
        final_judgement = judgement
        final_inspection = inspection
        if judgement["full_spec_pass"]:
            break

    assert final_judgement is not None
    assert first_judgement is not None
    repairs_used = max(0, len(attempts) - 1)
    all_failures = sorted(
        {
            category
            for attempt in attempts
            for category in attempt["failure_taxonomy"]
        }
    )
    record = {
        "engine": engine,
        "spec": spec_name,
        "category": str(spec["category"]),
        "trial": trial,
        "prompt_provenance": prompt_provenance(
            engine,
            spec_name,
            spec,
            trial,
        ),
        "source_metrics": source_metrics(first_source),
        "final_source_metrics": source_metrics(used_source),
        "first_run_execution_pass": first_execution_pass,
        "first_run_step_reimport_pass": first_judgement["step_reimport_pass"],
        "first_run_valid_brep_pass": first_judgement["valid_brep_pass"],
        "first_run_full_spec_pass": first_judgement["full_spec_pass"],
        "first_run_feature_checks_pass": first_judgement[
            "feature_checks_pass"
        ],
        "first_run_critical_dimensions_pass": first_judgement[
            "critical_dimensions_pass"
        ],
        "step_reimport_pass": final_judgement["step_reimport_pass"],
        "valid_brep_pass": final_judgement["valid_brep_pass"],
        "feature_checks_pass": final_judgement["feature_checks_pass"],
        "critical_dimensions_pass": final_judgement[
            "critical_dimensions_pass"
        ],
        "full_spec_pass": final_judgement["full_spec_pass"],
        "missing_feature_count": final_judgement["missing_feature_count"],
        "extra_feature_count": final_judgement["extra_feature_count"],
        "repair_rounds_used": repairs_used,
        "evaluation_wall_time_seconds": round(total_wall, 6),
        "wall_time_seconds": round(total_wall, 6),
        "failure_taxonomy": all_failures,
        "attempts": attempts,
        "final_inspection": final_inspection,
    }
    write_json(output / "trial.json", record)
    return record


def selected(values: list[str] | None, available: tuple[str, ...] | list[str]) -> list[str]:
    if not values:
        return list(available)
    unknown = set(values) - set(available)
    if unknown:
        raise ValueError(f"unknown selection(s): {', '.join(sorted(unknown))}")
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--engine", action="append", choices=ENGINES)
    parser.add_argument("--spec", action="append")
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument(
        "--max-repairs",
        type=int,
        default=0,
        choices=(0, 1, 2),
        help="Use optional trial-N-repair-R.py sources when present.",
    )
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    manifest = read_json(manifest_path)
    specs = specs_map(manifest)
    matrix = validate_manifest(manifest)
    engines = selected(args.engine, ENGINES)
    spec_names = selected(args.spec, list(specs))
    if args.trials < 1:
        raise ValueError("--trials must be at least 1")
    for environment in {POC_PYTHON, *( [ROOT_PYTHON] if "cadquery" in engines else [])}:
        if not environment.exists():
            raise RuntimeError(f"missing Python environment: {environment}")

    output_root = args.output_root.resolve()
    records: list[dict[str, Any]] = []
    for spec_name in spec_names:
        for trial in range(1, args.trials + 1):
            for engine in engines:
                print(f"[trial] {engine}/{spec_name}/{trial}", flush=True)
                record = run_trial(
                    manifest,
                    spec_name,
                    specs[spec_name],
                    engine,
                    trial,
                    output_root,
                    args.timeout_seconds,
                    args.max_repairs,
                )
                records.append(record)

    records_path = output_root / "trials.jsonl"
    records_path.parent.mkdir(parents=True, exist_ok=True)
    records_path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False) + "\n" for record in records
        ),
        encoding="utf-8",
    )
    result = write_reports(records_path, output_root, matrix=matrix)
    print(
        f"Report: {output_root / 'report.md'} "
        f"({len(result['trials'])} trials)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
