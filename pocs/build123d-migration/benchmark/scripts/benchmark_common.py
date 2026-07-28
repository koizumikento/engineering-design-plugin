#!/usr/bin/env python3
"""Shared utilities for the STR-231 agent-generation benchmark."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ENGINES = ("cadquery", "build123d")
CHECK_TAXONOMY = {
    "step_import": "step_import_error",
    "valid_brep": "invalid_geometry",
    "bbox_size": "bbox_mismatch",
    "bbox_min": "bbox_mismatch",
    "bbox_max": "bbox_mismatch",
    "solids": "solids_mismatch",
    "required_cylinder": "missing_cylinder",
    "point_probe": "point_probe_mismatch",
    "solid_bbox": "solid_bbox_mismatch",
    "volume_range": "volume_out_of_range",
    "extra_cylinders": "unexpected_cylinder",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def source_metrics(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    lines = data.decode("utf-8", errors="replace").splitlines()
    code_lines = [
        line
        for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    ]
    return {
        "path": str(path.resolve()),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "total_lines": len(lines),
        "nonblank_noncomment_lines": len(code_lines),
    }


def vector3(value: Any, field: str) -> list[float]:
    if isinstance(value, dict):
        try:
            return [float(value[axis]) for axis in ("x", "y", "z")]
        except KeyError as error:
            raise ValueError(f"{field} must contain x, y, z") from error
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return [float(component) for component in value]
    raise ValueError(f"{field} must be a 3-item list or x/y/z map")


def vector2(value: Any, field: str) -> list[float]:
    if isinstance(value, dict):
        keys = tuple(value)
        if len(keys) == 2:
            return [float(value[key]) for key in keys]
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return [float(component) for component in value]
    raise ValueError(f"{field} must be a 2-item list")


def close_vector(actual: Iterable[float], expected: Iterable[float], tolerance: float) -> bool:
    actual_values = list(actual)
    expected_values = list(expected)
    return len(actual_values) == len(expected_values) and all(
        math.isclose(left, right, abs_tol=tolerance, rel_tol=0.0)
        for left, right in zip(actual_values, expected_values, strict=True)
    )


def bbox_expectations(value: Any) -> dict[str, list[float]]:
    """Normalize size-only or min/max bounding-box expectations."""
    if isinstance(value, (list, tuple)):
        return {"size": vector3(value, "expected_bbox_mm")}
    if not isinstance(value, dict):
        raise ValueError("expected_bbox_mm must be a list or map")

    normalized: dict[str, list[float]] = {}
    aliases = {
        "size": ("size", "size_mm"),
        "min": ("min", "minimum", "min_mm"),
        "max": ("max", "maximum", "max_mm"),
    }
    for output_key, input_keys in aliases.items():
        selected = next((value[key] for key in input_keys if key in value), None)
        if selected is not None:
            normalized[output_key] = vector3(
                selected,
                f"expected_bbox_mm.{output_key}",
            )
    if not normalized:
        if all(axis in value for axis in ("x", "y", "z")):
            normalized["size"] = vector3(value, "expected_bbox_mm")
        else:
            raise ValueError("expected_bbox_mm needs size or min/max")
    return normalized


def tolerance(manifest: dict[str, Any], spec: dict[str, Any], key: str, default: float) -> float:
    tolerances = {
        **manifest.get("defaults", {}),
        **manifest.get("tolerances", {}),
    }
    spec_tolerances = spec.get("tolerances", {})
    aliases = {
        "bbox_tolerance_mm": ("linear_tolerance_mm",),
        "cylinder_tolerance_mm": ("radius_tolerance_mm",),
        "point_probe_tolerance_mm": ("point_tolerance_mm",),
    }
    for container, candidate in (
        (spec, key),
        (spec_tolerances, key),
        (manifest, key),
        (tolerances, key),
    ):
        if candidate in container:
            return float(container[candidate])
    for alias in aliases.get(key, ()):
        for container in (spec, spec_tolerances, manifest, tolerances):
            if alias in container:
                return float(container[alias])
    return default


def _axis_name(direction: Any) -> str:
    vector = vector3(direction, "cylindrical_features.axis.direction")
    absolute = [abs(value) for value in vector]
    index = max(range(3), key=absolute.__getitem__)
    if absolute[index] < 0.999 or any(
        value > 0.001 for offset, value in enumerate(absolute) if offset != index
    ):
        raise ValueError(f"cylinder axis must be cardinal, got {vector}")
    return ("x", "y", "z")[index]


def _normalize_case(case: dict[str, Any]) -> dict[str, Any]:
    expected = case.get("expected", {})
    normalized = dict(case)
    if expected:
        normalized["expected_bbox_mm"] = expected["bbox_mm"]
        normalized["expected_solids"] = expected["solid_count"]
        if "total_volume_mm3" in expected:
            normalized["volume_range_mm3"] = expected["total_volume_mm3"]
        normalized["expected_solid_bboxes"] = [
            {
                "id": solid.get("id"),
                "bbox": solid["bbox_mm"],
                "volume_range_mm3": solid.get("volume_mm3"),
                "transform": solid.get("transform"),
            }
            for solid in expected.get("solids", [])
        ]
        cylinders: list[dict[str, Any]] = []
        for feature in expected.get("cylindrical_features", []):
            axis = feature["axis"]
            axis_name = _axis_name(axis["direction"])
            point = vector3(axis["point"], "cylindrical_features.axis.point")
            if axis_name == "x":
                anchor = [point[1], point[2]]
            elif axis_name == "y":
                anchor = [point[0], point[2]]
            else:
                anchor = [point[0], point[1]]
            span = feature.get("span")
            cylinders.append(
                {
                    "id": feature.get("id"),
                    "kind": feature.get("kind"),
                    "axis": axis_name,
                    "radius_mm": feature["radius_mm"],
                    "anchor_mm": anchor,
                    "span_mm": (
                        [span["min"], span["max"]] if span is not None else None
                    ),
                    "requirement_ids": feature.get("requirement_ids", []),
                }
            )
        normalized["required_cylinders"] = cylinders
        normalized["point_probes"] = [
            {
                "id": probe.get("id"),
                "point": probe["point_mm"],
                "inside": str(probe["state"]).lower() == "inside",
                "solid": probe.get("solid"),
                "requirement_ids": probe.get("requirement_ids", []),
            }
            for probe in expected.get("point_probes", [])
        ]
        policy = expected.get("surface_policy", {})
        normalized["exact_cylinders"] = bool(
            policy.get("exact_cylinders", policy == "exact")
            if isinstance(policy, dict)
            else policy == "exact"
        )
    return normalized


def specs_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cases = manifest.get("cases")
    if isinstance(cases, list) and cases:
        result: dict[str, dict[str, Any]] = {}
        for case in cases:
            identifier = str(case["id"])
            if identifier in result:
                raise ValueError(f"duplicate case id: {identifier}")
            result[identifier] = _normalize_case(case)
        return result
    for key in ("specs", "models"):
        value = manifest.get(key)
        if isinstance(value, dict) and value:
            return {
                str(identifier): _normalize_case(case)
                for identifier, case in value.items()
            }
    raise ValueError("manifest must contain a non-empty specs or models map")


def requirement_ids(spec: dict[str, Any]) -> set[str]:
    raw = spec.get("requirement_ids", spec.get("requirements", []))
    if isinstance(raw, dict):
        return {str(value) for value in raw}
    result: set[str] = set()
    for value in raw:
        if isinstance(value, dict):
            identifier = value.get("id", value.get("requirement_id"))
            if identifier is not None:
                result.add(str(identifier))
        else:
            result.add(str(value))
    return result


def covered_requirement_ids(spec: dict[str, Any]) -> set[str]:
    explicit = spec.get(
        "requirement_coverage",
        spec.get("check_coverage", {}),
    )
    covered: set[str] = set()
    if isinstance(explicit, dict):
        covered.update(str(value) for value in explicit)
    elif isinstance(explicit, list):
        for value in explicit:
            if isinstance(value, dict):
                identifiers = value.get(
                    "requirement_ids",
                    [value.get("requirement_id", value.get("id"))],
                )
                covered.update(
                    str(identifier)
                    for identifier in identifiers
                    if identifier is not None
                )

    check_values: list[Any] = [
        spec.get("expected_bbox_mm"),
        spec.get("volume_range_mm3"),
        *spec.get("required_cylinders", []),
        *spec.get("point_probes", []),
        *spec.get("expected_solid_bboxes", []),
    ]
    for value in check_values:
        if not isinstance(value, dict):
            continue
        identifiers = value.get(
            "requirement_ids",
            [value.get("requirement_id")],
        )
        covered.update(
            str(identifier)
            for identifier in identifiers
            if identifier is not None
        )
    return covered


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate the benchmark's trial matrix and requirement/check traceability."""
    specs = specs_map(manifest)
    errors: list[str] = []
    expected_spec_count = int(
        manifest.get("expected_spec_count", manifest.get("benchmark", {}).get("specs", 10))
    )
    trials_per_engine = int(
        manifest.get(
            "trials_per_engine",
            manifest.get("benchmark", {}).get("trials_per_engine", 3),
        )
    )
    engines = manifest.get("engines", list(ENGINES))
    if engines != list(ENGINES) and set(engines) != set(ENGINES):
        errors.append(f"engines must be exactly {list(ENGINES)}")
    if len(specs) != expected_spec_count:
        errors.append(
            f"spec count is {len(specs)}; expected {expected_spec_count}"
        )
    if trials_per_engine != 3:
        errors.append(
            f"trials_per_engine is {trials_per_engine}; STR-231 requires 3"
        )

    for name, spec in specs.items():
        for field in ("expected_bbox_mm", "expected_solids"):
            if field not in spec:
                errors.append(f"{name}: missing {field}")
        try:
            if "expected_bbox_mm" in spec:
                bbox_expectations(spec["expected_bbox_mm"])
        except (TypeError, ValueError) as error:
            errors.append(f"{name}: {error}")
        if not isinstance(spec.get("required_cylinders", []), list):
            errors.append(f"{name}: required_cylinders must be a list")
        if not isinstance(spec.get("point_probes", []), list):
            errors.append(f"{name}: point_probes must be a list")
        category = spec.get("category")
        if not isinstance(category, str) or not category.strip():
            errors.append(f"{name}: missing non-empty category")
        requirements = requirement_ids(spec)
        coverage = covered_requirement_ids(spec)
        if not requirements:
            errors.append(f"{name}: no requirement IDs declared")
        missing_coverage = requirements - coverage
        unknown_coverage = coverage - requirements
        if missing_coverage:
            errors.append(
                f"{name}: requirements without checks: "
                + ", ".join(sorted(missing_coverage))
            )
        if unknown_coverage:
            errors.append(
                f"{name}: checks reference unknown requirements: "
                + ", ".join(sorted(unknown_coverage))
            )

    if errors:
        raise ValueError("invalid benchmark manifest:\n- " + "\n- ".join(errors))
    return {
        "spec_count": len(specs),
        "spec_names": sorted(specs),
        "engines": list(ENGINES),
        "trials_per_engine": trials_per_engine,
        "expected_trial_count": len(specs) * len(ENGINES) * trials_per_engine,
        "categories": sorted({spec["category"] for spec in specs.values()}),
    }


def classify_execution_failure(stdout: str, stderr: str, *, timed_out: bool) -> str:
    if timed_out:
        return "timeout"
    text = f"{stdout}\n{stderr}".lower()
    patterns = (
        ("syntaxerror", "syntax_error"),
        ("modulenotfounderror", "import_error"),
        ("importerror", "import_error"),
        ("does not publish", "missing_result"),
        ("変数が見つかりません", "missing_result"),
        ("fillet", "fillet_error"),
        ("shell", "shell_error"),
        ("selector", "selector_error"),
        ("boolean", "boolean_error"),
        ("export", "export_error"),
    )
    return next((category for token, category in patterns if token in text), "execution_error")


def _match_cylinders(
    actual: list[dict[str, Any]],
    required: list[dict[str, Any]],
    tolerance_mm: float,
) -> tuple[list[bool], set[int]]:
    matched_actual: set[int] = set()
    matches: list[bool] = []
    for item in required:
        axis = str(item["axis"]).lower()
        radius = float(item.get("radius_mm", item.get("radius")))
        anchor = vector2(
            item.get("anchor_mm", item.get("anchor")),
            "required_cylinders.anchor",
        )
        expected_span_value = item.get(
            "axial_span_mm",
            item.get("span_mm", item.get("span")),
        )
        expected_span = (
            vector2(expected_span_value, "required_cylinders.axial_span")
            if expected_span_value is not None
            else None
        )
        match = next(
            (
                index
                for index, cylinder in enumerate(actual)
                if index not in matched_actual
                and (
                    not item.get("kind")
                    or cylinder.get("kind") == str(item["kind"]).lower()
                )
                and cylinder["axis"] == axis
                and math.isclose(
                    float(cylinder["radius_mm"]),
                    radius,
                    abs_tol=tolerance_mm,
                    rel_tol=0.0,
                )
                and close_vector(cylinder["anchor_mm"], anchor, tolerance_mm)
                and (
                    expected_span is None
                    or close_vector(
                        cylinder.get("axial_span_mm", []),
                        expected_span,
                        tolerance_mm,
                    )
                )
            ),
            None,
        )
        matches.append(match is not None)
        if match is not None:
            matched_actual.add(match)
    return matches, matched_actual


def _match_solid_bboxes(
    actual: list[dict[str, Any]],
    expected: list[Any],
    tolerance_mm: float,
) -> list[bool]:
    used: set[int] = set()
    matches: list[bool] = []
    for value in expected:
        bbox_value = value.get("bbox", value) if isinstance(value, dict) else value
        wanted = bbox_expectations(bbox_value)
        expected_volume = (
            value.get("volume_range_mm3") if isinstance(value, dict) else None
        )
        match = None
        for index, candidate in enumerate(actual):
            if index in used:
                continue
            candidate_bbox = candidate.get("bbox_mm", candidate)
            bbox_matches = all(
                close_vector(candidate_bbox[key], vector, tolerance_mm)
                for key, vector in wanted.items()
            )
            if expected_volume is None:
                volume_matches = True
            elif isinstance(expected_volume, dict):
                minimum = float(
                    expected_volume.get(
                        "min",
                        expected_volume.get("minimum", -math.inf),
                    )
                )
                maximum = float(
                    expected_volume.get(
                        "max",
                        expected_volume.get("maximum", math.inf),
                    )
                )
                volume_matches = (
                    "volume_mm3" in candidate
                    and minimum <= candidate["volume_mm3"] <= maximum
                )
            else:
                minimum, maximum = (float(item) for item in expected_volume)
                volume_matches = (
                    "volume_mm3" in candidate
                    and minimum <= candidate["volume_mm3"] <= maximum
                )
            if bbox_matches and volume_matches:
                match = index
                break
        matches.append(match is not None)
        if match is not None:
            used.add(match)
    return matches


def judge_inspection(
    manifest: dict[str, Any],
    spec_name: str,
    spec: dict[str, Any],
    inspection: dict[str, Any] | None,
    *,
    execution_pass: bool,
) -> dict[str, Any]:
    """Evaluate one neutral STEP inspection against one benchmark spec."""
    checks: list[dict[str, Any]] = []

    def add(
        kind: str,
        passed: bool,
        detail: str,
        *,
        feature: bool = False,
        critical_dimension: bool = False,
    ) -> None:
        checks.append(
            {
                "kind": kind,
                "passed": bool(passed),
                "detail": detail,
                "feature": feature,
                "critical_dimension": critical_dimension,
                "failure_taxonomy": None if passed else CHECK_TAXONOMY[kind],
            }
        )

    add("step_import", inspection is not None, "neutral STEP import")
    if inspection is None:
        return {
            "spec": spec_name,
            "checks": checks,
            "step_reimport_pass": False,
            "valid_brep_pass": False,
            "feature_checks_pass": False,
            "critical_dimensions_pass": False,
            "full_spec_pass": False,
            "missing_feature_count": 0,
            "extra_feature_count": 0,
            "failure_taxonomy": ["step_import_error"],
        }

    add("valid_brep", bool(inspection["valid"]), f"actual={inspection['valid']}")
    invalid_solids = [
        index
        for index, solid in enumerate(inspection.get("solid_details", []), start=1)
        if not solid["valid"]
    ]
    if invalid_solids:
        checks[-1]["passed"] = False
        checks[-1]["detail"] += f" invalid_solids={invalid_solids}"
        checks[-1]["failure_taxonomy"] = "invalid_geometry"
    bbox_tol = tolerance(manifest, spec, "bbox_tolerance_mm", 0.05)
    expected_bbox = bbox_expectations(spec["expected_bbox_mm"])
    for key, expected in expected_bbox.items():
        actual = inspection["bbox_mm"][key]
        add(
            f"bbox_{key}",
            close_vector(actual, expected, bbox_tol),
            f"actual={actual} expected={expected} tolerance={bbox_tol}",
            critical_dimension=True,
        )

    expected_solids = int(spec["expected_solids"])
    actual_solids = int(inspection["topology"]["solids"])
    add(
        "solids",
        actual_solids == expected_solids,
        f"actual={actual_solids} expected={expected_solids}",
        feature=True,
    )

    required = []
    for item in spec.get("required_cylinders", []):
        required.extend([item] * int(item.get("count", 1)))
    cylinder_tol = tolerance(manifest, spec, "cylinder_tolerance_mm", 0.05)
    cylinder_matches, matched_actual = _match_cylinders(
        inspection.get("cylinder_features", inspection.get("cylinders", [])),
        required,
        cylinder_tol,
    )
    for index, (item, passed) in enumerate(
        zip(required, cylinder_matches, strict=True),
        start=1,
    ):
        add(
            "required_cylinder",
            passed,
            f"requirement={index} expected={json.dumps(item, ensure_ascii=False)}",
            feature=True,
            critical_dimension=True,
        )

    observed_cylinders = inspection.get(
        "cylinder_features",
        inspection.get("cylinders", []),
    )
    extra_cylinders = max(0, len(observed_cylinders) - len(matched_actual))
    if spec.get("exact_cylinders", False):
        add(
            "extra_cylinders",
            extra_cylinders == 0,
            f"unmatched_actual={extra_cylinders}",
            feature=True,
        )

    probe_tol = tolerance(manifest, spec, "point_probe_tolerance_mm", 1e-6)
    for index, probe in enumerate(spec.get("point_probes", []), start=1):
        point = vector3(probe["point"], "point_probes.point")
        observed = next(
            (
                item
                for item in inspection.get("point_probes", [])
                if close_vector(item["point_mm"], point, probe_tol)
            ),
            None,
        )
        expected_inside = bool(probe["inside"])
        passed = observed is not None and bool(observed["inside"]) == expected_inside
        add(
            "point_probe",
            passed,
            (
                f"probe={index} point={point} expected_inside={expected_inside} "
                f"actual={None if observed is None else observed['inside']}"
            ),
            feature=True,
        )

    solid_bboxes = spec.get("expected_solid_bboxes", [])
    solid_bbox_matches = _match_solid_bboxes(
        inspection.get(
            "solid_details",
            inspection.get("solid_bboxes_mm", []),
        ),
        solid_bboxes,
        bbox_tol,
    )
    for index, (value, passed) in enumerate(
        zip(solid_bboxes, solid_bbox_matches, strict=True),
        start=1,
    ):
        add(
            "solid_bbox",
            passed,
            f"requirement={index} expected={json.dumps(value, ensure_ascii=False)}",
            feature=True,
            critical_dimension=True,
        )

    if "volume_range_mm3" in spec:
        value = spec["volume_range_mm3"]
        if isinstance(value, dict):
            minimum = float(value.get("min", value.get("minimum", -math.inf)))
            maximum = float(value.get("max", value.get("maximum", math.inf)))
        else:
            minimum, maximum = (float(item) for item in value)
        actual_volume = float(inspection["volume_mm3"])
        add(
            "volume_range",
            minimum <= actual_volume <= maximum,
            f"actual={actual_volume} expected=[{minimum}, {maximum}]",
            critical_dimension=True,
        )

    feature_checks = [check for check in checks if check["feature"]]
    dimension_checks = [check for check in checks if check["critical_dimension"]]
    failures = [
        check["failure_taxonomy"]
        for check in checks
        if not check["passed"] and check["failure_taxonomy"]
    ]
    missing_features = sum(
        1
        for check in checks
        if not check["passed"]
        and check["kind"] in {"required_cylinder", "point_probe", "solid_bbox"}
    )
    return {
        "spec": spec_name,
        "checks": checks,
        "step_reimport_pass": True,
        "valid_brep_pass": bool(inspection["valid"]),
        "feature_checks_pass": all(check["passed"] for check in feature_checks),
        "critical_dimensions_pass": all(
            check["passed"] for check in dimension_checks
        ),
        "full_spec_pass": execution_pass and all(
            check["passed"] for check in checks
        ),
        "missing_feature_count": missing_features,
        "extra_feature_count": extra_cylinders,
        "failure_taxonomy": sorted(set(failures)),
    }


def rate(count: int, total: int) -> float:
    return count / total if total else 0.0


def summarize_trials(trials: list[dict[str, Any]]) -> dict[str, Any]:
    def group_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(records)
        walls = [float(record["wall_time_seconds"]) for record in records]
        repair_rounds = [int(record.get("repair_rounds_used", 0)) for record in records]
        taxonomies = Counter(
            category
            for record in records
            for category in record.get("failure_taxonomy", [])
        )
        return {
            "trials": total,
            "first_run_execution_pass": sum(
                bool(record["first_run_execution_pass"]) for record in records
            ),
            "first_run_execution_rate": rate(
                sum(bool(record["first_run_execution_pass"]) for record in records),
                total,
            ),
            "step_reimport_pass": sum(
                bool(record["first_run_step_reimport_pass"]) for record in records
            ),
            "step_reimport_rate": rate(
                sum(
                    bool(record["first_run_step_reimport_pass"])
                    for record in records
                ),
                total,
            ),
            "valid_brep_pass": sum(
                bool(record["first_run_valid_brep_pass"]) for record in records
            ),
            "valid_brep_rate": rate(
                sum(
                    bool(record["first_run_valid_brep_pass"])
                    for record in records
                ),
                total,
            ),
            "full_spec_pass": sum(
                bool(record["first_run_full_spec_pass"]) for record in records
            ),
            "full_spec_pass_rate": rate(
                sum(
                    bool(record["first_run_full_spec_pass"])
                    for record in records
                ),
                total,
            ),
            "feature_checks_pass": sum(
                bool(record["first_run_feature_checks_pass"])
                for record in records
            ),
            "feature_checks_pass_rate": rate(
                sum(
                    bool(record["first_run_feature_checks_pass"])
                    for record in records
                ),
                total,
            ),
            "critical_dimensions_pass": sum(
                bool(record["first_run_critical_dimensions_pass"])
                for record in records
            ),
            "critical_dimensions_pass_rate": rate(
                sum(
                    bool(record["first_run_critical_dimensions_pass"])
                    for record in records
                ),
                total,
            ),
            "final_feature_checks_pass": sum(
                bool(record["feature_checks_pass"]) for record in records
            ),
            "final_feature_checks_pass_rate": rate(
                sum(bool(record["feature_checks_pass"]) for record in records),
                total,
            ),
            "final_critical_dimensions_pass": sum(
                bool(record["critical_dimensions_pass"]) for record in records
            ),
            "final_critical_dimensions_pass_rate": rate(
                sum(bool(record["critical_dimensions_pass"]) for record in records),
                total,
            ),
            "final_full_spec_pass": sum(
                bool(record["full_spec_pass"]) for record in records
            ),
            "final_full_spec_pass_rate": rate(
                sum(bool(record["full_spec_pass"]) for record in records),
                total,
            ),
            "missing_feature_count": sum(
                int(record["missing_feature_count"]) for record in records
            ),
            "extra_feature_count": sum(
                int(record["extra_feature_count"]) for record in records
            ),
            "mean_wall_time_seconds": statistics.fmean(walls) if walls else 0.0,
            "median_wall_time_seconds": statistics.median(walls) if walls else 0.0,
            "mean_repair_rounds_used": (
                statistics.fmean(repair_rounds) if repair_rounds else 0.0
            ),
            "source_lines": sum(
                int(record["source_metrics"]["nonblank_noncomment_lines"])
                for record in records
            ),
            "unique_source_hashes": len(
                {record["source_metrics"]["sha256"] for record in records}
            ),
            "failure_taxonomy": dict(sorted(taxonomies.items())),
        }

    by_engine = {
        engine: group_summary(
            [trial for trial in trials if trial["engine"] == engine]
        )
        for engine in ENGINES
    }
    spec_names = sorted({trial["spec"] for trial in trials})
    by_spec = {
        spec: {
            engine: group_summary(
                [
                    trial
                    for trial in trials
                    if trial["spec"] == spec and trial["engine"] == engine
                ]
            )
            for engine in ENGINES
        }
        for spec in spec_names
    }
    category_names = sorted(
        {
            str(trial.get("category", trial["spec"]))
            for trial in trials
        }
    )
    by_category = {
        category: {
            engine: group_summary(
                [
                    trial
                    for trial in trials
                    if str(trial.get("category", trial["spec"])) == category
                    and trial["engine"] == engine
                ]
            )
            for engine in ENGINES
        }
        for category in category_names
    }
    return {
        "by_engine": by_engine,
        "by_spec": by_spec,
        "by_category": by_category,
    }
