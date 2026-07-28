#!/usr/bin/env python3
"""Inspect neutral STEP geometry with the candidate build123d environment."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path

from build123d import GeomType, Shape, import_step


def rounded(value: float) -> float:
    return round(float(value), 6)


def vector_list(vector) -> list[float]:
    return [rounded(vector.X), rounded(vector.Y), rounded(vector.Z)]


def cylinder_facts(shape: Shape) -> list[dict]:
    facts: list[dict] = []
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
        elif axis_name == "y":
            anchor = [position.X, position.Z]
        else:
            anchor = [position.X, position.Y]
        facts.append(
            {
                "axis": axis_name,
                "radius_mm": rounded(face.radius),
                "anchor_mm": [rounded(value) for value in anchor],
                "area_mm2": rounded(face.area),
            }
        )
    return sorted(
        facts,
        key=lambda item: (
            item["axis"],
            item["radius_mm"],
            item["anchor_mm"],
            item["area_mm2"],
        ),
    )


def inspect(step_path: Path) -> dict:
    shape = import_step(step_path)
    box = shape.bounding_box()
    return {
        "step": str(step_path.resolve()),
        "inspector": {
            "build123d": importlib.metadata.version("build123d"),
            "ocp": importlib.metadata.version("cadquery-ocp-novtk"),
        },
        "valid": bool(shape.is_valid),
        "bbox_mm": vector_list(box.size),
        "volume_mm3": rounded(shape.volume),
        "area_mm2": rounded(shape.area),
        "center_of_mass_mm": vector_list(shape.center()),
        "topology": {
            "solids": len(shape.solids()),
            "faces": len(shape.faces()),
            "edges": len(shape.edges()),
            "vertices": len(shape.vertices()),
        },
        "cylinders": cylinder_facts(shape),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()

    report = inspect(args.step)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
