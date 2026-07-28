#!/usr/bin/env python3
"""Read-only selector, measurement, alignment, frame, and diff inspection for STEP."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import OCP as build123d_occt
from build123d import CenterOf, GeomType, Shape, import_step

from cad_runner import (
    bounding_box_dict,
    inspect_shape,
    installed_version,
    location_dict,
    topology_dict,
)


SCHEMA_VERSION = 1
UNITS = "mm"
AXES = ("x", "y", "z")


class InspectionError(RuntimeError):
    """Raised when a STEP target or selector cannot be inspected safely."""


@dataclass
class Reference:
    selector: str
    kind: str
    value: Shape
    occurrence_selector: str
    parent_selector: str | None
    ordinal: int
    label: str = ""
    aliases: list[str] = field(default_factory=list)


def _rounded(value: float, digits: int = 12) -> float:
    result = round(float(value), digits)
    return 0.0 if result == -0.0 else result


def _vector_values(vector: Any) -> list[float]:
    return [
        _rounded(vector.X),
        _rounded(vector.Y),
        _rounded(vector.Z),
    ]


def _vector_mapping(vector: Any) -> dict[str, float]:
    return {
        axis: value for axis, value in zip(AXES, _vector_values(vector), strict=True)
    }


def _bbox_center(box: dict[str, float]) -> dict[str, float]:
    return {
        axis: _rounded((box[f"{axis}_min"] + box[f"{axis}_max"]) / 2) for axis in AXES
    }


def _center(value: Shape) -> dict[str, float]:
    try:
        return _vector_mapping(value.center(CenterOf.MASS))
    except (ValueError, RuntimeError, NotImplementedError):
        return _bbox_center(bounding_box_dict(value))


def _geom_type(value: Shape) -> str:
    geometry = getattr(value, "geom_type", None)
    if geometry is None:
        return type(value).__name__.lower()
    name = getattr(geometry, "name", None)
    return str(name or geometry).lower().removeprefix("geomtype.")


def _axis_payload(axis: Any) -> dict[str, dict[str, float]] | None:
    if axis is None:
        return None
    return {
        "position": _vector_mapping(axis.position),
        "direction": _vector_mapping(axis.direction),
    }


def _surface_payload(value: Shape) -> dict[str, Any]:
    payload: dict[str, Any] = {"geometry_type": _geom_type(value)}
    if getattr(value, "geom_type", None) == GeomType.PLANE:
        try:
            payload["normal"] = _vector_mapping(value.normal_at())
        except (ValueError, RuntimeError):
            pass
    try:
        raw_axis = getattr(value, "axis_of_rotation", None)
    except (ValueError, RuntimeError):
        raw_axis = None
    axis = _axis_payload(raw_axis)
    if axis is not None:
        payload["axis"] = axis
    try:
        radius = getattr(value, "radius", None)
    except (ValueError, RuntimeError):
        radius = None
    if radius is not None:
        payload["radius"] = _rounded(radius)
    return payload


def _axis_alignment(
    vector: dict[str, float], tolerance: float = 1e-6
) -> dict[str, Any] | None:
    components = [vector[axis] for axis in AXES]
    dominant = max(range(3), key=lambda index: abs(components[index]))
    if abs(abs(components[dominant]) - 1.0) > tolerance:
        return None
    if any(
        abs(component) > tolerance
        for index, component in enumerate(components)
        if index != dominant
    ):
        return None
    return {
        "axis": AXES[dominant],
        "sign": 1 if components[dominant] >= 0 else -1,
    }


def _location_payload(value: Shape) -> dict[str, dict[str, float]]:
    raw = location_dict(value)
    return {
        section: {axis: _rounded(number) for axis, number in values.items()}
        for section, values in raw.items()
    }


class ReferenceIndex:
    """Artifact-local selector index built from one imported STEP shape."""

    def __init__(self, root: Shape):
        self.root = root
        self.references: list[Reference] = []
        self.by_selector: dict[str, Reference] = {}
        self.occurrences: list[Reference] = []
        self.solids: list[Reference] = []
        self.faces: list[Reference] = []
        self.edges: list[Reference] = []
        self._visit_occurrence(root, "#o1", None, 1)
        self._add_single_occurrence_aliases()

    def _register(self, reference: Reference) -> None:
        self.references.append(reference)
        self.by_selector[reference.selector] = reference
        getattr(self, f"{reference.kind}s").append(reference)

    def _visit_occurrence(
        self,
        shape: Shape,
        selector: str,
        parent_selector: str | None,
        ordinal: int,
    ) -> None:
        label = str(shape.label or ("root" if parent_selector is None else ""))
        occurrence = Reference(
            selector=selector,
            kind="occurrence",
            value=shape,
            occurrence_selector=selector,
            parent_selector=parent_selector,
            ordinal=ordinal,
            label=label,
        )
        self._register(occurrence)

        children = list(shape.children)
        if children:
            for child_ordinal, child in enumerate(children, 1):
                self._visit_occurrence(
                    child,
                    f"{selector}.{child_ordinal}",
                    selector,
                    child_ordinal,
                )
            return

        for solid_ordinal, solid in enumerate(shape.solids(), 1):
            solid_selector = f"{selector}.s{solid_ordinal}"
            self._register(
                Reference(
                    selector=solid_selector,
                    kind="solid",
                    value=solid,
                    occurrence_selector=selector,
                    parent_selector=selector,
                    ordinal=solid_ordinal,
                    label=str(solid.label or label),
                )
            )
            for face_ordinal, face in enumerate(solid.faces(), 1):
                self._register(
                    Reference(
                        selector=f"{solid_selector}.f{face_ordinal}",
                        kind="face",
                        value=face,
                        occurrence_selector=selector,
                        parent_selector=solid_selector,
                        ordinal=face_ordinal,
                    )
                )
            for edge_ordinal, edge in enumerate(solid.edges(), 1):
                self._register(
                    Reference(
                        selector=f"{solid_selector}.e{edge_ordinal}",
                        kind="edge",
                        value=edge,
                        occurrence_selector=selector,
                        parent_selector=solid_selector,
                        ordinal=edge_ordinal,
                    )
                )

    def _add_single_occurrence_aliases(self) -> None:
        owners = {reference.occurrence_selector for reference in self.solids}
        if len(owners) != 1 or len(self.solids) != 1:
            return
        for reference in (*self.solids, *self.faces, *self.edges):
            suffix = reference.selector.split(".")[-1]
            alias = f"#{suffix}"
            if alias in self.by_selector:
                continue
            reference.aliases.append(alias)
            self.by_selector[alias] = reference

    def resolve(self, selector: str | None, *, default_root: bool = False) -> Reference:
        normalized = str(selector or "").strip()
        if not normalized:
            if default_root:
                return self.by_selector["#o1"]
            raise InspectionError("selector is required")
        if normalized.startswith("label:"):
            label = normalized.removeprefix("label:")
            matches = [
                reference for reference in self.occurrences if reference.label == label
            ]
            if not matches:
                raise InspectionError(f"selector {normalized!r} did not resolve")
            if len(matches) > 1:
                selectors = ", ".join(reference.selector for reference in matches)
                raise InspectionError(
                    f"selector {normalized!r} is ambiguous: {selectors}"
                )
            return matches[0]
        try:
            return self.by_selector[normalized]
        except KeyError as exc:
            raise InspectionError(f"selector {normalized!r} did not resolve") from exc

    def payload(self, reference: Reference) -> dict[str, Any]:
        box = {
            key: _rounded(value)
            for key, value in bounding_box_dict(reference.value).items()
        }
        payload: dict[str, Any] = {
            "selector": reference.selector,
            "aliases": reference.aliases,
            "kind": reference.kind,
            "ordinal": reference.ordinal,
            "label": reference.label or None,
            "parent_selector": reference.parent_selector,
            "occurrence_selector": reference.occurrence_selector,
            "center": _center(reference.value),
            "bounding_box": box,
        }
        if reference.kind == "occurrence":
            payload.update(
                {
                    "location": _location_payload(reference.value),
                    "topology": topology_dict(reference.value),
                    "valid": bool(reference.value.is_valid),
                }
            )
        elif reference.kind == "solid":
            payload.update(
                {
                    "topology": topology_dict(reference.value),
                    "volume": _rounded(reference.value.volume),
                    "area": _rounded(reference.value.area),
                }
            )
        else:
            payload.update(_surface_payload(reference.value))
            if reference.kind == "face":
                payload["area"] = _rounded(reference.value.area)
            elif reference.kind == "edge":
                payload["length"] = _rounded(reference.value.length)
        return payload


def _load_target(path: Path) -> tuple[Path, Shape, ReferenceIndex]:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise InspectionError(f"STEP target not found: {resolved}")
    if resolved.suffix.lower() not in {".step", ".stp"}:
        raise InspectionError("inspection target must use a .step or .stp suffix")
    try:
        shape = import_step(resolved)
    except Exception as exc:
        raise InspectionError(f"failed to import STEP target: {exc}") from exc
    if not isinstance(shape, Shape):
        raise InspectionError("STEP import did not return a build123d Shape")
    return resolved, shape, ReferenceIndex(shape)


def _related_runner_report(path: Path, step_sha256: str) -> dict[str, Any] | None:
    report_path = path.parent / "reports" / f"{path.stem}-cad-summary.json"
    if not report_path.is_file():
        return None
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "path": str(report_path),
            "valid_json": False,
        }
    source_path = Path(str(report.get("source", "")))
    source_hash_matches = None
    if source_path.is_file() and report.get("source_sha256"):
        source_hash_matches = (
            hashlib.sha256(source_path.read_bytes()).hexdigest()
            == report["source_sha256"]
        )
    report_step = report.get("step_artifact") or {}
    return {
        "path": str(report_path),
        "valid_json": True,
        "source": report.get("source"),
        "source_sha256": report.get("source_sha256"),
        "step_sha256": report_step.get("sha256"),
        "runtime": report.get("runtime"),
        "units": (report.get("export_settings") or {}).get("units"),
        "matches": {
            "source_sha256": source_hash_matches,
            "step_sha256": report_step.get("sha256") == step_sha256,
            "runtime": report.get("runtime")
            == {
                "python": platform.python_version(),
                "build123d": installed_version("build123d"),
                "build123d_occt": build123d_occt.__version__,
            },
            "units": (report.get("export_settings") or {}).get("units") == UNITS,
        },
    }


def _artifact_payload(path: Path, shape: Shape) -> dict[str, Any]:
    step_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "path": str(path),
        "sha256": step_sha256,
        "units": UNITS,
        "runtime": {
            "python": platform.python_version(),
            "build123d": installed_version("build123d"),
            "build123d_occt": build123d_occt.__version__,
        },
        "inspection": inspect_shape(shape),
        "related_runner_report": _related_runner_report(path, step_sha256),
    }


def _major_planes(
    index: ReferenceIndex,
    *,
    minimum_area_ratio: float,
    limit: int,
) -> list[dict[str, Any]]:
    planes = [
        reference
        for reference in index.faces
        if getattr(reference.value, "geom_type", None) == GeomType.PLANE
    ]
    if not planes:
        return []
    maximum_area = max(float(reference.value.area) for reference in planes)
    selected = [
        reference
        for reference in planes
        if float(reference.value.area) >= maximum_area * minimum_area_ratio
    ]
    selected.sort(key=lambda reference: float(reference.value.area), reverse=True)
    payloads: list[dict[str, Any]] = []
    for reference in selected[:limit]:
        payload = index.payload(reference)
        normal = payload.get("normal")
        alignment = _axis_alignment(normal) if isinstance(normal, dict) else None
        payloads.append(
            {
                "selector": reference.selector,
                "occurrence_selector": reference.occurrence_selector,
                "area": payload["area"],
                "center": payload["center"],
                "normal": normal,
                "axis_alignment": alignment,
                "coordinate": (
                    payload["center"][alignment["axis"]] if alignment else None
                ),
            }
        )
    return payloads


def _positioning_candidates(
    index: ReferenceIndex,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    candidates = [
        reference
        for reference in index.faces
        if getattr(reference.value, "geom_type", None)
        in {GeomType.PLANE, GeomType.CYLINDER}
    ]
    candidates.sort(key=lambda reference: float(reference.value.area), reverse=True)
    return [index.payload(reference) for reference in candidates[:limit]]


def inspect_refs(args: argparse.Namespace) -> dict[str, Any]:
    path, shape, index = _load_target(args.target)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "command": "refs",
        "artifact": _artifact_payload(path, shape),
        "occurrences": [index.payload(reference) for reference in index.occurrences],
        "solids": [index.payload(reference) for reference in index.solids],
        "major_planes": _major_planes(
            index,
            minimum_area_ratio=args.plane_min_area_ratio,
            limit=args.plane_limit,
        ),
        "positioning_candidates": _positioning_candidates(
            index,
            limit=args.positioning_limit,
        ),
        "selector_stability": (
            "artifact-local; selectors may change after topology or STEP changes"
        ),
    }
    if args.selector:
        payload["selection"] = index.payload(index.resolve(args.selector))
    if args.topology:
        payload["faces"] = [index.payload(reference) for reference in index.faces]
        payload["edges"] = [index.payload(reference) for reference in index.edges]
    return payload


def _point(reference: Reference) -> dict[str, float]:
    surface = _surface_payload(reference.value)
    axis = surface.get("axis")
    if isinstance(axis, dict):
        return axis["position"]
    return _center(reference.value)


def _expectation_payload(
    actual: float,
    *,
    expected: float | None,
    tolerance: float,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "actual": _rounded(actual),
        "units": UNITS,
        "expected": expected,
        "tolerance": tolerance,
    }
    if expected is not None:
        delta = abs(actual - expected)
        payload.update(
            {
                "delta": _rounded(delta),
                "passed": delta <= tolerance,
            }
        )
    return payload


def inspect_measure(args: argparse.Namespace) -> dict[str, Any]:
    path, shape, index = _load_target(args.target)
    from_reference = index.resolve(args.from_selector)
    from_payload = index.payload(from_reference)
    if args.extent:
        if args.to_selector:
            raise InspectionError("--extent cannot be combined with --to")
        actual = from_payload["bounding_box"][f"{args.extent}_len"]
        measurement = {
            "kind": "bounding_box_extent",
            "axis": args.extent,
            **_expectation_payload(
                actual,
                expected=args.expected,
                tolerance=args.tolerance,
            ),
        }
        to_payload = None
    else:
        if not args.to_selector:
            raise InspectionError("pair measurement requires --to or use --extent")
        to_reference = index.resolve(args.to_selector)
        to_payload = index.payload(to_reference)
        from_point = _point(from_reference)
        to_point = _point(to_reference)
        offset = {axis: _rounded(to_point[axis] - from_point[axis]) for axis in AXES}
        euclidean = math.sqrt(sum(value * value for value in offset.values()))
        if args.axis == "distance":
            actual = euclidean
        else:
            actual = offset[args.axis]
        measurement = {
            "kind": (
                "euclidean_distance" if args.axis == "distance" else "signed_axis_delta"
            ),
            "axis": args.axis,
            "center_offset": offset,
            "euclidean_distance": _rounded(euclidean),
            **_expectation_payload(
                actual,
                expected=args.expected,
                tolerance=args.tolerance,
            ),
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "command": "measure",
        "artifact": _artifact_payload(path, shape),
        "from": from_payload,
        "to": to_payload,
        "measurement": measurement,
    }


def _infer_aligned_axis(*vectors: dict[str, float]) -> str:
    alignments = [_axis_alignment(vector) for vector in vectors]
    if not alignments or any(alignment is None for alignment in alignments):
        raise InspectionError("could not infer an axis; pass --axis x, y, or z")
    axes = {alignment["axis"] for alignment in alignments if alignment}
    if len(axes) != 1:
        raise InspectionError("selected references do not share an axis")
    return axes.pop()


def _parallel_relation(
    first: dict[str, float],
    second: dict[str, float],
    tolerance: float,
) -> dict[str, Any]:
    dot = sum(first[axis] * second[axis] for axis in AXES)
    parallel = abs(abs(dot) - 1.0) <= tolerance
    return {
        "dot": _rounded(dot),
        "parallel": parallel,
        "relation": "same" if dot >= 0 else "opposed",
    }


def inspect_align(args: argparse.Namespace) -> dict[str, Any]:
    path, shape, index = _load_target(args.target)
    moving = index.resolve(args.moving)
    target = index.resolve(args.target_selector)
    moving_payload = index.payload(moving)
    target_payload = index.payload(target)
    moving_point = _point(moving)
    target_point = _point(target)
    translation = {axis: 0.0 for axis in AXES}
    vector_relation = None
    resolved_axis = args.axis

    if args.mode == "center":
        for axis in AXES:
            if args.axis is None or args.axis == axis:
                translation[axis] = _rounded(target_point[axis] - moving_point[axis])
    elif args.mode == "flush":
        moving_normal = moving_payload.get("normal")
        target_normal = target_payload.get("normal")
        if not isinstance(moving_normal, dict) or not isinstance(target_normal, dict):
            raise InspectionError("flush alignment requires two planar face selectors")
        axis = args.axis or _infer_aligned_axis(moving_normal, target_normal)
        resolved_axis = axis
        vector_relation = _parallel_relation(
            moving_normal,
            target_normal,
            args.angular_tolerance,
        )
        if not vector_relation["parallel"]:
            raise InspectionError("flush face normals are not parallel")
        target_sign = 1
        alignment = _axis_alignment(target_normal)
        if alignment and alignment["axis"] == axis:
            target_sign = alignment["sign"]
        translation[axis] = _rounded(
            target_point[axis] + (args.offset * target_sign) - moving_point[axis]
        )
    else:
        moving_axis = moving_payload.get("axis")
        target_axis = target_payload.get("axis")
        if not isinstance(moving_axis, dict) or not isinstance(target_axis, dict):
            raise InspectionError(
                "coaxial alignment requires two cylindrical face selectors"
            )
        axis = args.axis or _infer_aligned_axis(
            moving_axis["direction"],
            target_axis["direction"],
        )
        resolved_axis = axis
        vector_relation = _parallel_relation(
            moving_axis["direction"],
            target_axis["direction"],
            args.angular_tolerance,
        )
        if not vector_relation["parallel"]:
            raise InspectionError("cylindrical axes are not parallel")
        for candidate in AXES:
            if candidate != axis:
                translation[candidate] = _rounded(
                    target_axis["position"][candidate]
                    - moving_axis["position"][candidate]
                )

    magnitude = math.sqrt(sum(value * value for value in translation.values()))
    return {
        "schema_version": SCHEMA_VERSION,
        "command": "align",
        "artifact": _artifact_payload(path, shape),
        "mode": args.mode,
        "axis": resolved_axis,
        "moving": moving_payload,
        "target": target_payload,
        "alignment": {
            "translation_delta": translation,
            "magnitude": _rounded(magnitude),
            "units": UNITS,
            "tolerance": args.tolerance,
            "within_tolerance": magnitude <= args.tolerance,
            "vector_relation": vector_relation,
            "read_only": True,
        },
    }


def inspect_frame(args: argparse.Namespace) -> dict[str, Any]:
    path, shape, index = _load_target(args.target)
    reference = index.resolve(args.selector, default_root=True)
    occurrence = index.resolve(reference.occurrence_selector)
    selection = index.payload(reference)
    surface = _surface_payload(reference.value)
    primary_axis = surface.get("axis")
    if primary_axis is None and surface.get("normal") is not None:
        primary_axis = {
            "position": _point(reference),
            "direction": surface["normal"],
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "command": "frame",
        "artifact": _artifact_payload(path, shape),
        "selection": selection,
        "world_frame": {
            **_location_payload(occurrence.value),
            "occurrence_selector": occurrence.selector,
            "selection_position": _point(reference),
            "selection_axis": primary_axis,
        },
    }


def _delta_mapping(
    left: dict[str, float],
    right: dict[str, float],
) -> dict[str, float]:
    return {
        key: _rounded(right[key] - left[key]) for key in sorted(set(left) & set(right))
    }


def _labels(index: ReferenceIndex) -> list[str]:
    return sorted(
        reference.label
        for reference in index.occurrences
        if reference.label and reference.selector != "#o1"
    )


def _component_transforms(index: ReferenceIndex) -> list[dict[str, Any]]:
    return [
        {
            "selector": reference.selector,
            "label": reference.label or None,
            "location": _location_payload(reference.value),
        }
        for reference in index.occurrences
        if reference.selector != "#o1"
    ]


def _plane_signature(plane: dict[str, Any], tolerance: float) -> tuple[Any, ...]:
    quantum = max(tolerance, 1e-12)
    alignment = plane.get("axis_alignment")
    coordinate = plane.get("coordinate")
    if not alignment or coordinate is None:
        normal = plane.get("normal") or {}
        return (
            "other",
            *(round(float(normal.get(axis, 0.0)) / quantum) for axis in AXES),
            round(float(plane["area"]) / quantum),
        )
    return (
        alignment["axis"],
        alignment["sign"],
        round(float(coordinate) / quantum),
        round(float(plane["area"]) / quantum),
    )


def _occurrence_diff(
    left_index: ReferenceIndex,
    right_index: ReferenceIndex,
    tolerance: float,
) -> list[dict[str, Any]]:
    left = {item["selector"]: item for item in _component_transforms(left_index)}
    right = {item["selector"]: item for item in _component_transforms(right_index)}
    results: list[dict[str, Any]] = []
    for selector in sorted(set(left) | set(right)):
        if selector not in left:
            results.append(
                {
                    "selector": selector,
                    "change": "added",
                    "right": right[selector],
                }
            )
            continue
        if selector not in right:
            results.append(
                {
                    "selector": selector,
                    "change": "removed",
                    "left": left[selector],
                }
            )
            continue
        position_delta = _delta_mapping(
            left[selector]["location"]["position"],
            right[selector]["location"]["position"],
        )
        orientation_delta = _delta_mapping(
            left[selector]["location"]["orientation"],
            right[selector]["location"]["orientation"],
        )
        changed = (
            any(
                abs(value) > tolerance
                for value in (*position_delta.values(), *orientation_delta.values())
            )
            or left[selector]["label"] != right[selector]["label"]
        )
        results.append(
            {
                "selector": selector,
                "change": "changed" if changed else "unchanged",
                "left_label": left[selector]["label"],
                "right_label": right[selector]["label"],
                "position_delta": position_delta,
                "orientation_delta": orientation_delta,
            }
        )
    return results


def inspect_diff(args: argparse.Namespace) -> dict[str, Any]:
    left_path, left_shape, left_index = _load_target(args.before)
    right_path, right_shape, right_index = _load_target(args.after)
    left_inspection = inspect_shape(left_shape)
    right_inspection = inspect_shape(right_shape)
    left_bbox = left_inspection["bounding_box"]
    right_bbox = right_inspection["bounding_box"]
    left_labels = _labels(left_index)
    right_labels = _labels(right_index)
    occurrence_changes = _occurrence_diff(
        left_index,
        right_index,
        args.tolerance,
    )
    left_planes = _major_planes(
        left_index,
        minimum_area_ratio=args.plane_min_area_ratio,
        limit=args.plane_limit,
    )
    right_planes = _major_planes(
        right_index,
        minimum_area_ratio=args.plane_min_area_ratio,
        limit=args.plane_limit,
    )
    left_plane_set = {_plane_signature(plane, args.tolerance) for plane in left_planes}
    right_plane_set = {
        _plane_signature(plane, args.tolerance) for plane in right_planes
    }
    bbox_delta = _delta_mapping(left_bbox, right_bbox)
    topology_delta = _delta_mapping(
        left_inspection["topology"],
        right_inspection["topology"],
    )
    volume_delta = _rounded(right_inspection["volume"] - left_inspection["volume"])
    changed = (
        abs(volume_delta) > args.tolerance
        or any(abs(value) > args.tolerance for value in bbox_delta.values())
        or any(value != 0 for value in topology_delta.values())
        or left_labels != right_labels
        or any(item["change"] != "unchanged" for item in occurrence_changes)
        or left_plane_set != right_plane_set
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "command": "diff",
        "before": _artifact_payload(left_path, left_shape),
        "after": _artifact_payload(right_path, right_shape),
        "diff": {
            "changed": changed,
            "tolerance": args.tolerance,
            "units": UNITS,
            "bounding_box_delta": bbox_delta,
            "volume_delta": volume_delta,
            "topology_delta": topology_delta,
            "labels": {
                "before": left_labels,
                "after": right_labels,
                "added": sorted(set(right_labels) - set(left_labels)),
                "removed": sorted(set(left_labels) - set(right_labels)),
            },
            "component_transforms": occurrence_changes,
            "major_planes": {
                "before": left_planes,
                "after": right_planes,
                "added_count": len(right_plane_set - left_plane_set),
                "removed_count": len(left_plane_set - right_plane_set),
            },
        },
    }


def _text_output(payload: dict[str, Any]) -> str:
    command = payload["command"]
    if command == "refs":
        return (
            f"{payload['artifact']['path']}: "
            f"{len(payload['occurrences'])} occurrences, "
            f"{len(payload['solids'])} solids, "
            f"{len(payload['major_planes'])} major planes"
        )
    if command == "measure":
        measurement = payload["measurement"]
        status = f", passed={measurement['passed']}" if "passed" in measurement else ""
        return (
            f"{measurement['kind']}: {measurement['actual']:.6g} "
            f"{measurement['units']}{status}"
        )
    if command == "align":
        alignment = payload["alignment"]
        return (
            f"{payload['mode']} delta={alignment['translation_delta']} "
            f"magnitude={alignment['magnitude']:.6g} {alignment['units']}"
        )
    if command == "frame":
        frame = payload["world_frame"]
        return (
            f"{payload['selection']['selector']}: "
            f"position={frame['position']} orientation={frame['orientation']}"
        )
    diff = payload["diff"]
    return (
        f"changed={diff['changed']} volume_delta={diff['volume_delta']:.6g} "
        f"{diff['units']}^3"
    )


def _add_output_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="output format; JSON is the machine-readable contract",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only build123d STEP inspection")
    subparsers = parser.add_subparsers(dest="command", required=True)

    refs_parser = subparsers.add_parser("refs", help="enumerate local selectors")
    refs_parser.add_argument("target", type=Path)
    refs_parser.add_argument("selector", nargs="?")
    refs_parser.add_argument("--topology", action="store_true")
    refs_parser.add_argument("--plane-min-area-ratio", type=float, default=0.05)
    refs_parser.add_argument("--plane-limit", type=int, default=12)
    refs_parser.add_argument("--positioning-limit", type=int, default=24)
    _add_output_arguments(refs_parser)
    refs_parser.set_defaults(handler=inspect_refs)

    measure_parser = subparsers.add_parser("measure", help="measure local refs")
    measure_parser.add_argument("target", type=Path)
    measure_parser.add_argument("--from", dest="from_selector", required=True)
    measure_parser.add_argument("--to", dest="to_selector")
    measure_parser.add_argument(
        "--axis",
        choices=(*AXES, "distance"),
        default="distance",
    )
    measure_parser.add_argument("--extent", choices=AXES)
    measure_parser.add_argument("--expected", type=float)
    measure_parser.add_argument("--tolerance", type=float, default=1e-6)
    _add_output_arguments(measure_parser)
    measure_parser.set_defaults(handler=inspect_measure)

    align_parser = subparsers.add_parser(
        "align",
        help="compute a read-only alignment delta",
    )
    align_parser.add_argument("target", type=Path)
    align_parser.add_argument("--moving", required=True)
    align_parser.add_argument("--target", dest="target_selector", required=True)
    align_parser.add_argument(
        "--mode",
        choices=("flush", "center", "coaxial"),
        default="flush",
    )
    align_parser.add_argument("--axis", choices=AXES)
    align_parser.add_argument("--offset", type=float, default=0.0)
    align_parser.add_argument("--tolerance", type=float, default=1e-6)
    align_parser.add_argument("--angular-tolerance", type=float, default=1e-6)
    _add_output_arguments(align_parser)
    align_parser.set_defaults(handler=inspect_align)

    frame_parser = subparsers.add_parser("frame", help="inspect a world frame")
    frame_parser.add_argument("target", type=Path)
    frame_parser.add_argument("selector", nargs="?")
    _add_output_arguments(frame_parser)
    frame_parser.set_defaults(handler=inspect_frame)

    diff_parser = subparsers.add_parser("diff", help="compare two STEP artifacts")
    diff_parser.add_argument("before", type=Path)
    diff_parser.add_argument("after", type=Path)
    diff_parser.add_argument("--tolerance", type=float, default=1e-6)
    diff_parser.add_argument("--plane-min-area-ratio", type=float, default=0.05)
    diff_parser.add_argument("--plane-limit", type=int, default=12)
    _add_output_arguments(diff_parser)
    diff_parser.set_defaults(handler=inspect_diff)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if getattr(args, "tolerance", 0) < 0:
        parser.error("--tolerance must be non-negative")
    try:
        payload = args.handler(args)
    except Exception as exc:
        error_payload = {
            "schema_version": SCHEMA_VERSION,
            "command": args.command,
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
        print(json.dumps(error_payload, indent=2), file=sys.stderr)
        return 2
    print(
        json.dumps(payload, indent=2, ensure_ascii=False)
        if args.format == "json"
        else _text_output(payload)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
