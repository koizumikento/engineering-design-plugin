#!/usr/bin/env python3
"""Aggregate STR-231 trial records and produce JSON and Markdown reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from benchmark_common import (
    ENGINES,
    read_json,
    summarize_trials,
    validate_manifest,
    write_json,
)


def percent(value: float) -> str:
    return f"{value:.1%}"


def migration_gate(
    summary: dict[str, Any],
    matrix: dict[str, Any] | None,
    trials: list[dict[str, Any]],
) -> dict[str, Any]:
    cq = summary["by_engine"]["cadquery"]
    b3d = summary["by_engine"]["build123d"]
    full_spec_delta = (
        b3d["full_spec_pass_rate"] - cq["full_spec_pass_rate"]
    )
    cq_repairs = cq["mean_repair_rounds_used"]
    b3d_repairs = b3d["mean_repair_rounds_used"]
    repair_reduction = (
        (cq_repairs - b3d_repairs) / cq_repairs if cq_repairs > 0 else 0.0
    )
    critical_regression = (
        b3d["critical_dimensions_pass_rate"]
        < cq["critical_dimensions_pass_rate"]
    )
    improved_categories = sum(
        summary["by_category"][category]["build123d"][
            "full_spec_pass_rate"
        ]
        > summary["by_category"][category]["cadquery"]["full_spec_pass_rate"]
        for category in summary["by_category"]
    )
    completed_trials = sum(
        summary["by_engine"][engine]["trials"] for engine in ENGINES
    )
    expected_trials = (
        matrix["expected_trial_count"] if matrix is not None else completed_trials
    )
    actual_trial_keys = {
        (trial["engine"], trial["spec"], int(trial["trial"]))
        for trial in trials
    }
    expected_trial_keys = (
        {
            (engine, spec, trial)
            for engine in matrix["engines"]
            for spec in matrix["spec_names"]
            for trial in range(1, matrix["trials_per_engine"] + 1)
        }
        if matrix is not None
        else set()
    )
    enough_data = (
        matrix is not None
        and len(trials) == expected_trials
        and actual_trial_keys == expected_trial_keys
    )
    primary_gate = full_spec_delta >= 0.10 or repair_reduction >= 0.25
    return {
        "enough_data": enough_data,
        "full_spec_rate_delta": full_spec_delta,
        "repair_round_reduction": repair_reduction,
        "critical_dimension_regression": critical_regression,
        "improved_category_count": improved_categories,
        "completed_trial_count": completed_trials,
        "expected_trial_count": expected_trials,
        "passed": (
            enough_data
            and primary_gate
            and not critical_regression
            and improved_categories >= 3
        ),
        "note": (
            "This mechanical gate does not attest prompt isolation, token parity, "
            "or human-edit controls; verify those controls before a migration decision."
        ),
    }


def markdown_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    gate = result["migration_gate"]
    lines = [
        "# STR-231 CadQuery vs build123d agent-generation benchmark",
        "",
        f"Completed trials: **{len(result['trials'])}**",
        "",
        "## Engine summary",
        "",
        "| Engine | Trials | First execution | First valid BREP | First full spec | Final full spec | First/final features | First/final critical dimensions | Mean repairs | Mean eval time |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for engine in ENGINES:
        value = summary["by_engine"][engine]
        lines.append(
            "| {engine} | {trials} | {execution} | {valid} | {full} | "
            "{final_full} | {first_features}/{final_features} | "
            "{first_dimensions}/{final_dimensions} | {repairs:.2f} | {wall:.3f}s |".format(
                engine=engine,
                trials=value["trials"],
                execution=percent(value["first_run_execution_rate"]),
                valid=percent(value["valid_brep_rate"]),
                full=percent(value["full_spec_pass_rate"]),
                final_full=percent(value["final_full_spec_pass_rate"]),
                first_features=percent(value["feature_checks_pass_rate"]),
                final_features=percent(value["final_feature_checks_pass_rate"]),
                first_dimensions=percent(
                    value["critical_dimensions_pass_rate"]
                ),
                final_dimensions=percent(
                    value["final_critical_dimensions_pass_rate"]
                ),
                repairs=value["mean_repair_rounds_used"],
                wall=value["mean_wall_time_seconds"],
            )
        )

    lines.extend(
        [
            "",
            "## Per-spec full-spec pass rate",
            "",
            "| Spec | CadQuery | build123d | Delta |",
            "|---|---:|---:|---:|",
        ]
    )
    for spec, engines in summary["by_spec"].items():
        cq_rate = engines["cadquery"]["full_spec_pass_rate"]
        b3d_rate = engines["build123d"]["full_spec_pass_rate"]
        lines.append(
            f"| {spec} | {percent(cq_rate)} | {percent(b3d_rate)} | "
            f"{percent(b3d_rate - cq_rate)} |"
        )

    lines.extend(
        [
            "",
            "## Failure taxonomy",
            "",
            "| Engine | Category | Count |",
            "|---|---|---:|",
        ]
    )
    failure_rows = 0
    for engine in ENGINES:
        for category, count in summary["by_engine"][engine][
            "failure_taxonomy"
        ].items():
            lines.append(f"| {engine} | `{category}` | {count} |")
            failure_rows += 1
    if failure_rows == 0:
        lines.append("| — | No failures | 0 |")

    lines.extend(
        [
            "",
            "## Mechanical migration gate",
            "",
            f"- Result: **{'PASS' if gate['passed'] else 'NOT MET'}**",
            f"- Trial completeness: {gate['completed_trial_count']} / {gate['expected_trial_count']}",
            f"- Full-spec rate delta: {percent(gate['full_spec_rate_delta'])}",
            f"- Repair-round reduction: {percent(gate['repair_round_reduction'])}",
            f"- Critical-dimension regression: {gate['critical_dimension_regression']}",
            f"- Distinct categories improved: {gate['improved_category_count']}",
            f"- Control note: {gate['note']}",
            "",
            "## Trial details",
            "",
            "| Engine | Spec | Trial | First execution | First STEP import | First valid | First full spec | Final full spec | Repairs | Failure taxonomy |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for trial in sorted(
        result["trials"],
        key=lambda item: (item["spec"], item["trial"], item["engine"]),
    ):
        failures = ", ".join(trial["failure_taxonomy"]) or "—"
        lines.append(
            "| {engine} | {spec} | {trial} | {execution} | {step} | "
            "{valid} | {full} | {final_full} | {repairs} | {failures} |".format(
                engine=trial["engine"],
                spec=trial["spec"],
                trial=trial["trial"],
                execution="PASS" if trial["first_run_execution_pass"] else "FAIL",
                step="PASS" if trial["first_run_step_reimport_pass"] else "FAIL",
                valid="PASS" if trial["first_run_valid_brep_pass"] else "FAIL",
                full="PASS" if trial["first_run_full_spec_pass"] else "FAIL",
                final_full="PASS" if trial["full_spec_pass"] else "FAIL",
                repairs=trial["repair_rounds_used"],
                failures=failures,
            )
        )
    return "\n".join(lines) + "\n"


def load_records(records_path: Path) -> list[dict[str, Any]]:
    if not records_path.exists():
        return []
    return [
        json.loads(line)
        for line in records_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_reports(
    records_path: Path,
    output_root: Path,
    *,
    matrix: dict[str, Any] | None = None,
) -> dict[str, Any]:
    trials = load_records(records_path)
    summary = summarize_trials(trials)
    result = {
        "trials": trials,
        "matrix": matrix,
        "summary": summary,
        "migration_gate": migration_gate(summary, matrix, trials),
    }
    write_json(output_root / "benchmark.json", result)
    (output_root / "report.md").write_text(
        markdown_report(result),
        encoding="utf-8",
    )
    write_json(output_root / "summary.json", summary)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    matrix = (
        validate_manifest(read_json(args.manifest.resolve()))
        if args.manifest
        else None
    )
    result = write_reports(
        args.records.resolve(),
        args.output_root.resolve(),
        matrix=matrix,
    )
    print(markdown_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
