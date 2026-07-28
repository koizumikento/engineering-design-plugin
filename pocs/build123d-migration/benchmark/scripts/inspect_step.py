#!/usr/bin/env python3
"""Inspect a generated STEP file in the neutral build123d/OCP environment."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
from typing import Any

from build123d import GeomType, Shape, Vector, import_step
from OCP.Geom import Geom_RectangularTrimmedSurface


def rounded(value: float) -> float:
    return round(float(value), 6)


def vector3(vector: Any) -> list[float]:
    return [rounded(vector.X), rounded(vector.Y), rounded(vector.Z)]


def bbox(shape: Shape) -> dict[str, list[float]]:
    box = shape.bounding_box()
    return {
        "size": vector3(box.size),
        "min": vector3(box.min),
        "max": vector3(box.max),
    }


def cylinder_radius(face) -> float:
    """Return a cylinder radius, including rectangularly trimmed surfaces."""
    radius = face.radius
    if radius is not None:
        return float(radius)
    surface = face.geom_adaptor()
    while isinstance(surface, Geom_RectangularTrimmedSurface):
        surface = surface.BasisSurface()
    if not hasattr(surface, "Radius"):
        raise ValueError("cylindrical face does not expose a radius")
    return float(surface.Radius())


def cylinder_facts(shape: Shape) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for face in shape.faces():
        if face.geom_type != GeomType.CYLINDER:
            continue
        axis = face.axis_of_rotation
        direction = axis.direction
        components = [abs(direction.X), abs(direction.Y), abs(direction.Z)]
        axis_index = max(range(3), key=components.__getitem__)
        axis_name = ("x", "y", "z")[axis_index]
        position = axis.position
        if axis_name == "x":
            anchor = [position.Y, position.Z]
            span = [face.bounding_box().min.X, face.bounding_box().max.X]
        elif axis_name == "y":
            anchor = [position.X, position.Z]
            span = [face.bounding_box().min.Y, face.bounding_box().max.Y]
        else:
            anchor = [position.X, position.Y]
            span = [face.bounding_box().min.Z, face.bounding_box().max.Z]
        center = face.center()
        axis_position = axis.position
        axis_direction = axis.direction
        relative = center - axis_position
        projection = axis_direction * relative.dot(axis_direction)
        radial = relative - projection
        kind = "external" if face.normal_at().dot(radial) > 0 else "internal"
        facts.append(
            {
                "kind": kind,
                "axis": axis_name,
                "radius_mm": rounded(cylinder_radius(face)),
                "anchor_mm": [rounded(value) for value in anchor],
                "axial_span_mm": [rounded(value) for value in span],
                "area_mm2": rounded(face.area),
            }
        )
    return sorted(
        facts,
        key=lambda item: (
            item["axis"],
            item["radius_mm"],
            item["anchor_mm"],
            item["axial_span_mm"],
            item["area_mm2"],
        ),
    )


def aggregate_cylinders(facts: list[dict[str, Any]], tolerance: float = 1e-5) -> list[dict[str, Any]]:
    """Merge touching coaxial face fragments into observable cylinder features."""
    groups: dict[tuple[Any, ...], list[list[float]]] = {}
    for fact in facts:
        key = (
            fact["kind"],
            fact["axis"],
            fact["radius_mm"],
            *fact["anchor_mm"],
        )
        groups.setdefault(key, []).append(fact["axial_span_mm"])

    features: list[dict[str, Any]] = []
    for key, intervals in groups.items():
        merged: list[list[float]] = []
        for start, end in sorted(intervals):
            if merged and start <= merged[-1][1] + tolerance:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        for span in merged:
            features.append(
                {
                    "kind": key[0],
                    "axis": key[1],
                    "radius_mm": key[2],
                    "anchor_mm": [key[3], key[4]],
                    "axial_span_mm": [rounded(value) for value in span],
                }
            )
    return sorted(
        features,
        key=lambda item: (
            item["axis"],
            item["radius_mm"],
            item["anchor_mm"],
            item["axial_span_mm"],
        ),
    )


def inspect(step_path: Path, probes: list[list[float]]) -> dict[str, Any]:
    shape = import_step(step_path)
    solids = shape.solids()
    cylinders = cylinder_facts(shape)
    return {
        "step": str(step_path.resolve()),
        "inspector": {
            "build123d": importlib.metadata.version("build123d"),
            "ocp": importlib.metadata.version("cadquery-ocp-novtk"),
        },
        "valid": bool(shape.is_valid),
        "bbox_mm": bbox(shape),
        "volume_mm3": rounded(shape.volume),
        "area_mm2": rounded(shape.area),
        "center_of_mass_mm": vector3(shape.center()),
        "topology": {
            "solids": len(solids),
            "faces": len(shape.faces()),
            "edges": len(shape.edges()),
            "vertices": len(shape.vertices()),
        },
        "top_level_shape_types": [
            str(item.shape_type) for item in shape.get_top_level_shapes()
        ],
        "solid_bboxes_mm": [bbox(solid) for solid in solids],
        "solid_details": [
            {
                "valid": bool(solid.is_valid),
                "bbox_mm": bbox(solid),
                "volume_mm3": rounded(solid.volume),
            }
            for solid in solids
        ],
        "cylinders": cylinders,
        "cylinder_features": aggregate_cylinders(cylinders),
        "point_probes": [
            {
                "point_mm": [rounded(value) for value in point],
                "inside": bool(shape.is_inside(Vector(*point))),
            }
            for point in probes
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument(
        "--probe",
        action="append",
        nargs=3,
        type=float,
        metavar=("X", "Y", "Z"),
        default=[],
    )
    args = parser.parse_args()

    try:
        report = inspect(args.step.resolve(), args.probe)
    except Exception as error:
        failure = {
            "step": str(args.step.resolve()),
            "error_type": type(error).__name__,
            "error": str(error),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(failure, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(failure, ensure_ascii=False))
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["valid"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
