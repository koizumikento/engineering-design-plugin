#!/usr/bin/env python3
"""Execute, export, and validate a build123d mechanical CAD source module."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any

import OCP as build123d_occt
from build123d import BuildPart, CenterOf, Shape, export_step, export_stl, import_step


RESULT_NAMES = ("result", "assembly", "model", "shape", "part")
METADATA_NAME = "cad_metadata"
EXPECTATIONS_NAME = "cad_expectations"


def load_source(source: Path) -> tuple[Shape, dict[str, Any], dict[str, Any]]:
    """Load one source module and its optional metadata/check contract."""
    module_name = f"engineering_design_build123d_{source.stem}_{hashlib.sha256(source.read_bytes()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load build123d source: {source}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    result = next(
        (getattr(module, name) for name in RESULT_NAMES if hasattr(module, name)),
        None,
    )
    if result is None:
        raise ValueError(f"{source} does not publish any of {RESULT_NAMES}")
    if isinstance(result, BuildPart):
        result = result.part
    if not isinstance(result, Shape):
        raise TypeError(
            "build123d source must publish a Shape or BuildPart; "
            f"received {type(result).__name__}"
        )

    metadata = getattr(module, METADATA_NAME, {})
    expectations = getattr(module, EXPECTATIONS_NAME, {})
    if not isinstance(metadata, dict):
        raise TypeError(f"{METADATA_NAME} must be a dictionary")
    if not isinstance(expectations, dict):
        raise TypeError(f"{EXPECTATIONS_NAME} must be a dictionary")
    return result, metadata, expectations


def vector_dict(vector: Any) -> dict[str, float]:
    return {
        "x": float(vector.X),
        "y": float(vector.Y),
        "z": float(vector.Z),
    }


def location_dict(shape: Shape) -> dict[str, dict[str, float]]:
    return {
        "position": vector_dict(shape.location.position),
        "orientation": vector_dict(shape.location.orientation),
    }


def topology_dict(shape: Shape) -> dict[str, int]:
    return {
        "solids": len(shape.solids()),
        "faces": len(shape.faces()),
        "edges": len(shape.edges()),
        "vertices": len(shape.vertices()),
    }


def bounding_box_dict(shape: Shape) -> dict[str, float]:
    box = shape.bounding_box()
    return {
        "x_len": float(box.size.X),
        "y_len": float(box.size.Y),
        "z_len": float(box.size.Z),
        "x_min": float(box.min.X),
        "x_max": float(box.max.X),
        "y_min": float(box.min.Y),
        "y_max": float(box.max.Y),
        "z_min": float(box.min.Z),
        "z_max": float(box.max.Z),
    }


def component_dict(shape: Shape) -> dict[str, Any]:
    joints = getattr(shape, "joints", {})
    return {
        "label": str(shape.label or type(shape).__name__),
        "valid": bool(shape.is_valid),
        "location": location_dict(shape),
        "center_of_mass": vector_dict(shape.center(CenterOf.MASS)),
        "bounding_box": bounding_box_dict(shape),
        "topology": topology_dict(shape),
        "joints": sorted(str(label) for label in joints),
    }


def inspect_shape(shape: Shape) -> dict[str, Any]:
    components = [component_dict(child) for child in shape.children]
    return {
        "label": str(shape.label or type(shape).__name__),
        "valid": bool(shape.is_valid),
        "volume": float(shape.volume),
        "area": float(shape.area),
        "center_of_mass": vector_dict(shape.center(CenterOf.MASS)),
        "bounding_box": bounding_box_dict(shape),
        "topology": topology_dict(shape),
        "components": components,
    }


def _check_number(
    checks: list[dict[str, Any]],
    *,
    name: str,
    actual: float,
    expected: float,
    tolerance: float,
) -> None:
    delta = abs(float(actual) - float(expected))
    checks.append(
        {
            "name": name,
            "passed": delta <= tolerance,
            "actual": float(actual),
            "expected": float(expected),
            "tolerance": tolerance,
            "delta": delta,
        }
    )


def evaluate_expectations(
    inspection: dict[str, Any],
    expectations: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate an intentionally small, engine-specific source contract."""
    checks: list[dict[str, Any]] = []
    tolerance = float(expectations.get("tolerance_mm", 1e-6))

    for key, expected in expectations.get("topology", {}).items():
        actual = inspection["topology"].get(key)
        checks.append(
            {
                "name": f"topology.{key}",
                "passed": actual == expected,
                "actual": actual,
                "expected": expected,
            }
        )

    for key, expected in expectations.get("bounding_box", {}).items():
        _check_number(
            checks,
            name=f"bounding_box.{key}",
            actual=inspection["bounding_box"][key],
            expected=expected,
            tolerance=tolerance,
        )

    components = {
        component["label"]: component for component in inspection["components"]
    }
    for label, expected_component in expectations.get("components", {}).items():
        component = components.get(label)
        checks.append(
            {
                "name": f"components.{label}.present",
                "passed": component is not None,
                "actual": component is not None,
                "expected": True,
            }
        )
        if component is None:
            continue

        for key, expected in expected_component.get("position", {}).items():
            _check_number(
                checks,
                name=f"components.{label}.position.{key}",
                actual=component["location"]["position"][key],
                expected=expected,
                tolerance=tolerance,
            )
        for key, expected in expected_component.get("bounding_box", {}).items():
            _check_number(
                checks,
                name=f"components.{label}.bounding_box.{key}",
                actual=component["bounding_box"][key],
                expected=expected,
                tolerance=tolerance,
            )

    return {
        "defined": bool(expectations),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def installed_version(*distribution_names: str) -> str | None:
    for name in distribution_names:
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            continue
    return None


def export_model(
    shape: Shape,
    *,
    output: Path,
    name: str,
    formats: list[str],
) -> list[str]:
    exported: list[str] = []
    for output_format in formats:
        output_path = output / f"{name}.{output_format}"
        if output_format == "step":
            export_step(shape, output_path)
        elif output_format == "stl":
            export_stl(
                shape,
                output_path,
                tolerance=0.05,
                angular_tolerance=0.1,
            )
        else:
            raise ValueError(
                f"unsupported build123d format {output_format!r}; use step or stl"
            )
        exported.append(str(output_path))
    return exported


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute and validate a build123d mechanical CAD model"
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=Path("outputs"))
    parser.add_argument("--name")
    parser.add_argument("--format", default="step,stl")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--fail-on-invalid", action="store_true")
    parser.add_argument(
        "--fail-on-check",
        action="store_true",
        help="exit non-zero on invalid source/STEP geometry or failed expectations",
    )
    args = parser.parse_args()

    source = args.source.resolve()
    if not source.is_file():
        print(f"Error: source not found: {source}", file=sys.stderr)
        return 1

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    name = args.name or source.stem
    formats = [item.strip().lower() for item in args.format.split(",") if item.strip()]

    try:
        shape, metadata, expectations = load_source(source)
        source_inspection = inspect_shape(shape)
        exported_files = export_model(
            shape,
            output=output,
            name=name,
            formats=formats,
        )

        step_path = output / f"{name}.step"
        if "step" not in formats:
            raise ValueError("STEP export is required for neutral reimport validation")
        reimported = import_step(step_path)
        step_inspection = inspect_shape(reimported)
        expectation_result = evaluate_expectations(step_inspection, expectations)

        report = {
            "engine": "build123d",
            "source": str(source),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "runtime": {
                "python": platform.python_version(),
                "build123d": installed_version("build123d"),
                "build123d_occt": build123d_occt.__version__,
            },
            "metadata": metadata,
            "export_settings": {
                "units": "mm",
                "step": {"neutral_reimport_required": True},
                "stl": {
                    "linear_tolerance": 0.05,
                    "angular_tolerance": 0.1,
                },
            },
            "validation": source_inspection,
            "step_reimport": step_inspection,
            "expectations": expectation_result,
            "exported_files": exported_files,
            "report": None,
        }

        if args.report:
            report_dir = output / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            report_path = report_dir / f"{name}-cad-summary.json"
            report["report"] = str(report_path)
            report_path.write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        print(json.dumps(report, indent=2, ensure_ascii=False))
        invalid = not source_inspection["valid"] or not step_inspection["valid"]
        failed_checks = not expectation_result["passed"]
        if args.fail_on_check and (invalid or failed_checks):
            return 2
        if args.fail_on_invalid and invalid:
            return 2
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "engine": "build123d",
                    "source": str(source),
                    "error": f"{type(exc).__name__}: {exc}",
                    "fallback": None,
                },
                indent=2,
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
