#!/usr/bin/env python3
"""Compare CadQuery and build123d neutral STEP inspection reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def close_values(actual: list[float], expected: list[float], tolerance: float) -> bool:
    return len(actual) == len(expected) and all(
        abs(left - right) <= tolerance
        for left, right in zip(actual, expected, strict=True)
    )


def has_cylinder(
    cylinders: list[dict],
    required: dict,
    tolerance: float,
) -> bool:
    return any(
        cylinder["axis"] == required["axis"]
        and abs(cylinder["radius_mm"] - required["radius_mm"]) <= tolerance
        and close_values(
            cylinder["anchor_mm"],
            required["anchor_mm"],
            tolerance,
        )
        for cylinder in cylinders
    )


def source_metrics(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    code_lines = [
        line
        for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    ]
    text = "\n".join(lines)
    return {
        "total_lines": len(lines),
        "nonblank_noncomment_lines": len(code_lines),
        "assertions": text.count("assert "),
        "exception_handlers": text.count("except"),
        "string_selector_tokens": sum(
            text.count(token)
            for token in ('.faces("', '.edges("', ".filter(")
        ),
    }


def compare_model(
    name: str,
    config: dict,
    poc_root: Path,
    output_root: Path,
    bbox_tolerance: float,
    cylinder_tolerance: float,
    volume_tolerance: float,
) -> dict:
    reports = {}
    for engine in ("cadquery", "build123d"):
        path = output_root / "inspections" / engine / f"{name}.json"
        reports[engine] = json.loads(path.read_text(encoding="utf-8"))

    checks: list[dict] = []

    def add(check: str, passed: bool, detail: str) -> None:
        checks.append({"check": check, "passed": passed, "detail": detail})

    for engine, report in reports.items():
        add(f"{engine}:valid", report["valid"], str(report["valid"]))
        add(
            f"{engine}:bbox",
            close_values(
                report["bbox_mm"],
                config["expected_bbox_mm"],
                bbox_tolerance,
            ),
            f"actual={report['bbox_mm']} expected={config['expected_bbox_mm']}",
        )
        add(
            f"{engine}:solids",
            report["topology"]["solids"] == config["expected_solids"],
            (
                f"actual={report['topology']['solids']} "
                f"expected={config['expected_solids']}"
            ),
        )
        for index, required in enumerate(config["required_cylinders"], start=1):
            add(
                f"{engine}:cylinder:{index}",
                has_cylinder(
                    report["cylinders"],
                    required,
                    cylinder_tolerance,
                ),
                json.dumps(required, ensure_ascii=False),
            )

    left_volume = reports["cadquery"]["volume_mm3"]
    right_volume = reports["build123d"]["volume_mm3"]
    relative_volume_difference = abs(left_volume - right_volume) / max(
        abs(left_volume),
        abs(right_volume),
        1.0,
    )
    add(
        "cross-engine:volume",
        relative_volume_difference <= volume_tolerance,
        f"relative_difference={relative_volume_difference:.6f}",
    )
    add(
        "cross-engine:bbox",
        close_values(
            reports["cadquery"]["bbox_mm"],
            reports["build123d"]["bbox_mm"],
            bbox_tolerance,
        ),
        (
            f"cadquery={reports['cadquery']['bbox_mm']} "
            f"build123d={reports['build123d']['bbox_mm']}"
        ),
    )

    source_data = {
        engine: source_metrics(poc_root / config[f"{engine}_source"])
        for engine in ("cadquery", "build123d")
    }
    return {
        "name": name,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "reports": reports,
        "source_metrics": source_data,
        "relative_volume_difference": relative_volume_difference,
    }


def markdown_report(result: dict) -> str:
    lines = [
        "# CadQuery to build123d PoC comparison",
        "",
        f"Overall result: **{'PASS' if result['passed'] else 'FAIL'}**",
        "",
        "| Model | Result | CadQuery volume | build123d volume | Relative delta | CadQuery / build123d code lines |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for model in result["models"]:
        reports = model["reports"]
        metrics = model["source_metrics"]
        lines.append(
            "| {name} | {result} | {cq:.3f} | {b3d:.3f} | {delta:.4%} | {cq_lines} / {b3d_lines} |".format(
                name=model["name"],
                result="PASS" if model["passed"] else "FAIL",
                cq=reports["cadquery"]["volume_mm3"],
                b3d=reports["build123d"]["volume_mm3"],
                delta=model["relative_volume_difference"],
                cq_lines=metrics["cadquery"]["nonblank_noncomment_lines"],
                b3d_lines=metrics["build123d"]["nonblank_noncomment_lines"],
            )
        )
    lines.extend(["", "## Check details", ""])
    for model in result["models"]:
        failed = [check for check in model["checks"] if not check["passed"]]
        lines.append(f"### {model['name']}")
        lines.append("")
        if not failed:
            lines.append("- All configured geometry checks passed.")
        else:
            for check in failed:
                lines.append(f"- FAIL `{check['check']}`: {check['detail']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    poc_root = manifest_path.parent
    output_root = args.output_root.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    models = [
        compare_model(
            name,
            config,
            poc_root,
            output_root,
            manifest["bbox_tolerance_mm"],
            manifest["cylinder_tolerance_mm"],
            manifest["volume_relative_tolerance"],
        )
        for name, config in manifest["models"].items()
    ]
    result = {"passed": all(model["passed"] for model in models), "models": models}

    json_path = output_root / "comparison.json"
    markdown_path = output_root / "comparison.md"
    json_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(markdown_report(result) + "\n", encoding="utf-8")
    print(markdown_report(result))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
