#!/usr/bin/env python3
"""Judge a neutral STEP inspection against one STR-231 manifest spec."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmark_common import judge_inspection, read_json, specs_map, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--inspection", type=Path, required=True)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument(
        "--execution-failed",
        action="store_true",
        help="Include an execution failure in full-spec evaluation.",
    )
    args = parser.parse_args()

    manifest = read_json(args.manifest)
    specs = specs_map(manifest)
    if args.spec not in specs:
        raise SystemExit(f"unknown spec: {args.spec}")
    inspection = read_json(args.inspection)
    if "error" in inspection:
        inspection = None
    result = judge_inspection(
        manifest,
        args.spec,
        specs[args.spec],
        inspection,
        execution_pass=not args.execution_failed,
    )
    write_json(args.output, result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["full_spec_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
