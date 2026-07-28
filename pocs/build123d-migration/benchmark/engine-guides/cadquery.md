# CadQuery trial guide

Runtime: CadQuery 2.x in the repository root environment.

The submitted module must import `cadquery as cq` and publish a `result`
variable containing a `cq.Workplane`, `cq.Shape`, `cq.Compound`, or
`cq.Assembly`. Do not export files.

Common exact-solid patterns:

```python
import cadquery as cq

box = cq.Workplane("XY").box(x, y, z, centered=(True, True, False))
cylinder = cq.Workplane("XY", origin=(cx, cy, z0)).circle(radius).extrude(height)
part = box.union(cylinder).cut(tool).clean()
```

- Use `cq.Workplane("XY", origin=(x, y, z))` for an explicit datum.
- `box(..., centered=(True, True, False))` places the bottom at the workplane.
- Use `pushPoints([...]).circle(r).extrude(h)` for repeated Z-axis cylinders.
- Build X/Y-axis cylinders on `"YZ"`/`"XZ"` workplanes with explicit origins.
- Boolean operations are `.union(other)`, `.cut(other)`, and
  `.intersect(other)`.
- Use `.edges(selector).fillet(radius)` and `.edges(selector).chamfer(distance)`
  only when the selected edges are unambiguous.
- A slot may be constructed from a rectangle and two cylinders, then cut.
- A hollow open box may be made by subtracting an explicitly dimensioned
  cavity tool; no shell API is required.
- Translate a shape with `.translate((x, y, z))`.
- Preserve separate assembly solids with
  `cq.Compound.makeCompound([shape1.val(), shape2.val(), ...])`.
- Validate locally in source only with `assert result.val().isValid()` for a
  Workplane or `assert result.isValid()` for a Shape. The harness performs the
  authoritative validation.

Reference: <https://cadquery.readthedocs.io/>
