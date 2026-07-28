# build123d implementation

Read this reference when writing or repairing any mechanical CAD source.

## API style

Use Algebra mode by default when explicit object construction, Boolean
expressions, and transforms make the design direct:

```python
from build123d import Align, Box, Cylinder, Pos

base = Box(80, 50, 4, align=(Align.CENTER, Align.CENTER, Align.MIN))
holes = Pos(-30, 0, 0) * Cylinder(2, 6)
holes += Pos(30, 0, 0) * Cylinder(2, 6)
result = (base - holes).clean()
```

Use `BuildLine`, `BuildSketch`, and `BuildPart` when workplane context,
profile-driven operations, repeated `Locations`, or last-operation selection
make the construction easier to read. Keep each feature as a named variable or
function so failures localize.

## Source contract

Every source module must publish:

- `result`: a valid build123d `Shape`; use a labeled `Compound` for assemblies;
- optional `cad_metadata`: units, coordinate convention, and source relationships;
- optional `cad_expectations`: independently checkable STEP properties.

The supported expectation keys are:

```python
cad_expectations = {
    "tolerance_mm": 1e-6,
    "topology": {"solids": 2},
    "bounding_box": {"x_len": 60.0, "y_len": 40.0, "z_len": 7.0},
    "components": {
        "base": {
            "position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "bounding_box": {"z_min": 0.0, "z_max": 4.0},
        },
    },
}
```

Use native labels on the root and every direct assembly child. Use concise
functional names such as `base`, `lid`, `shaft`, or `bearing:front`; do not rely
on topology order as identity.

## Coordinates, placement, and joints

Define each part in a documented local coordinate system before placing it.
Prefer a functional datum such as a mounting face, shaft axis, or bolt-pattern
centre over an arbitrary origin.

Use the simplest relationship that preserves design intent:

- `RigidJoint`: fixed seating, mounting, or coaxial placement;
- `RevoluteJoint`: hinge or shaft pose;
- `LinearJoint`: slider pose;
- `CylindricalJoint`: combined rotation and translation;
- explicit `Location`: simple static patterns that do not need a joint.

For `connect_to()`, call the joint on the fixed/root part and pass the joint on
the moving part:

```python
base.joints["lid_seat"].connect_to(lid.joints["underside"])
```

This resolves one source-level placement. The exported STEP is required to
preserve the resulting static transform and labels, not a live editable
constraint.

For parts and assemblies, pass axis-specific primitive alignment. For a Z-up
cylinder or box, a scalar `Align.MIN` also changes X and Y alignment:

```python
align=(Align.CENTER, Align.CENTER, Align.MIN)
```

## Modeling and export

Keep controlling dimensions in named variables. Build closed positive-volume
solids, apply major additions and cuts before fillets, and overshoot through-cut
tools so coincident faces do not destabilize Boolean operations.

Run the root production environment:

```bash
uv sync
uv run python scripts/cad_runner.py \
  <input.py> -o <outputs/> --report --fail-on-check
```

The committed root runtime and lock require Python 3.11.x and build123d 0.11.1.

The runner:

- validates the source BREP;
- exports STEP and STL;
- reimports STEP in the same pinned build123d/`build123d_occt` runtime;
- checks validity, bbox, topology, direct-child labels and transforms;
- evaluates the source module's `cad_expectations`;
- records source SHA-256 and the `build123d`/`build123d_occt` runtime versions.

Generate visual evidence through the neutral STEP artifact:

```bash
uv run python scripts/preview_generator.py <outputs/model.step> \
  -o <outputs/> --all-views
```

## Failure handling

Report whether a failure was source execution, invalid BREP, STEP
export/reimport, a missing label, a placement mismatch, or another expectation
failure. Do not suppress the error or export a known-invalid result.

## Primary references

- [build123d introduction](https://build123d.readthedocs.io/en/latest/introduction.html)
- [Builder mode](https://build123d.readthedocs.io/en/latest/key_concepts_builder.html)
- [Algebra mode](https://build123d.readthedocs.io/en/latest/key_concepts_algebra.html)
- [build123d joints](https://build123d.readthedocs.io/en/latest/joints.html)
- [build123d import/export](https://build123d.readthedocs.io/en/latest/import_export.html)
