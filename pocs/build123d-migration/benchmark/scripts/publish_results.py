#!/usr/bin/env python3
"""Publish a compact, commit-ready STR-231 result set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from benchmark_common import write_json


REPO_ROOT = Path(__file__).resolve().parents[4]


def compact_trial(trial: dict[str, Any]) -> dict[str, Any]:
    source = Path(trial["source_metrics"]["path"])
    return {
        "engine": trial["engine"],
        "spec": trial["spec"],
        "category": trial["category"],
        "trial": trial["trial"],
        "prompt_sha256": trial["prompt_provenance"]["sha256"],
        "rendered_task_sha256": trial["prompt_provenance"][
            "rendered_task_sha256"
        ],
        "source": str(source.relative_to(REPO_ROOT)),
        "source_sha256": trial["source_metrics"]["sha256"],
        "source_lines": trial["source_metrics"][
            "nonblank_noncomment_lines"
        ],
        "first_run_execution_pass": trial["first_run_execution_pass"],
        "first_run_step_reimport_pass": trial[
            "first_run_step_reimport_pass"
        ],
        "first_run_valid_brep_pass": trial["first_run_valid_brep_pass"],
        "first_run_feature_checks_pass": trial[
            "first_run_feature_checks_pass"
        ],
        "first_run_critical_dimensions_pass": trial[
            "first_run_critical_dimensions_pass"
        ],
        "first_run_full_spec_pass": trial["first_run_full_spec_pass"],
        "final_full_spec_pass": trial["full_spec_pass"],
        "repair_rounds_used": trial["repair_rounds_used"],
        "evaluation_wall_time_seconds": trial[
            "evaluation_wall_time_seconds"
        ],
        "failure_taxonomy": trial["failure_taxonomy"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    benchmark = json.loads(args.benchmark.read_text(encoding="utf-8"))
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    compact_trials = [compact_trial(trial) for trial in benchmark["trials"]]
    write_json(output / "trials.json", {"trials": compact_trials})
    write_json(
        output / "summary.json",
        {
            "issue": "STR-231",
            "status": "complete",
            "trial_count": len(compact_trials),
            "pilot": {
                "status": "excluded",
                "reason": [
                    "build123d guide used scalar Align.MIN for cylinders, shifting X/Y axes",
                    "clevis arm width equaled hole diameter and made the one-solid oracle impossible",
                ],
                "retained_output": "outputs/str231-agent-benchmark-pilot/",
            },
            "controls": {
                "manual_edits_before_first_evaluation": 0,
                "maximum_repair_rounds": 2,
                "repairs_used": 0,
                "exact_model_build": "NOT_EVALUATED",
                "token_usage": "NOT_EVALUATED",
                "agent_generation_wall_time": "NOT_EVALUATED",
            },
            "summary": benchmark["summary"],
            "migration_gate": benchmark["migration_gate"],
            "decision": "retain CadQuery; build123d did not improve generation accuracy",
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
