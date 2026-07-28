#!/usr/bin/env python3
"""Execute and report a build123d model in the isolated PoC environment."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import sys
from pathlib import Path

from build123d import BuildPart, Shape, export_step, export_stl


RESULT_NAMES = ("result", "model", "shape", "part", "assembly")


def load_model(source: Path) -> Shape:
    module_name = f"build123d_poc_{source.stem}"
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load model source: {source}")
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
        raise TypeError(f"unsupported build123d result type: {type(result).__name__}")
    return result


def vector_dict(vector) -> dict[str, float]:
    return {"x": float(vector.X), "y": float(vector.Y), "z": float(vector.Z)}


def validate(shape: Shape) -> dict:
    box = shape.bounding_box()
    return {
        "valid": bool(shape.is_valid),
        "volume": float(shape.volume),
        "area": float(shape.area),
        "center_of_mass": vector_dict(shape.center()),
        "bounding_box": {
            "x_len": float(box.size.X),
            "y_len": float(box.size.Y),
            "z_len": float(box.size.Z),
            "x_min": float(box.min.X),
            "x_max": float(box.max.X),
            "y_min": float(box.min.Y),
            "y_max": float(box.max.Y),
            "z_min": float(box.min.Z),
            "z_max": float(box.max.Z),
        },
        "topology": {
            "solids": len(shape.solids()),
            "faces": len(shape.faces()),
            "edges": len(shape.edges()),
            "vertices": len(shape.vertices()),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--name")
    args = parser.parse_args()

    source = args.source.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    name = args.name or source.stem

    shape = load_model(source)
    validation = validate(shape)
    step_path = output / f"{name}.step"
    stl_path = output / f"{name}.stl"
    export_step(shape, step_path, timestamp="2026-07-28T00:00:00Z")
    export_stl(shape, stl_path, tolerance=0.05, angular_tolerance=0.1)

    report = {
        "engine": "build123d",
        "source": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "runtime": {
            "python": platform.python_version(),
            "build123d": importlib.metadata.version("build123d"),
            "ocp": importlib.metadata.version("cadquery-ocp-novtk"),
        },
        "export_settings": {
            "units": "mm",
            "step": {
                "write_pcurves": True,
                "precision_mode": "average",
                "timestamp": "2026-07-28T00:00:00Z",
            },
            "stl": {
                "linear_tolerance": 0.05,
                "angular_tolerance": 0.1,
                "ascii": False,
            },
        },
        "validation": validation,
        "exported_files": [str(step_path), str(stl_path)],
    }
    report_path = output / f"{name}-cad-summary.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if validation["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
