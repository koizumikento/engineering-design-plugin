# build123d trial guide

Runtime: build123d 0.11.1 in the isolated PoC environment.

The submitted module must import from `build123d` and publish a `result`
variable containing a `Shape` such as `Part` or `Compound`. Do not export
files.

Common exact-solid patterns:

```python
from build123d import Align, Box, Cylinder, Pos

box = Box(x, y, z, align=(Align.CENTER, Align.CENTER, Align.MIN))
cylinder = Pos(cx, cy, z0) * Cylinder(
    radius,
    height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
part = (box + cylinder - tool).clean()
```

- Use `Pos(x, y, z) * shape` for an explicit translation.
- `Box(..., align=(Align.CENTER, Align.CENTER, Align.MIN))` places the bottom
  at Z = 0.
- `Cylinder(radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN))`
  keeps the cylinder axis on local X=0/Y=0 and extends along local +Z.
- Do not use scalar `align=Align.MIN` for a positioned cylinder: it also
  shifts the X/Y axis by one radius.
- Use `Plane.YZ` or `Plane.XZ` with an explicit `Pos`/`Rot`, or rotate a
  cylinder with `Rot`, for X/Y-axis features.
- Boolean operations are `+` or `.fuse()`, `-` or `.cut()`, and `&`.
- Algebra operations `fillet(edges, radius=...)` and
  `chamfer(edges, length=...)` accept an explicit edge list.
- A slot may be constructed from a rectangle and two circles, extruded, then
  cut.
- A hollow open box may be made by subtracting an explicitly dimensioned
  cavity tool; no shell API is required.
- Preserve separate assembly solids with `Compound(children=[part1, part2,
  ...])`.
- Validate locally in source only with `assert result.is_valid`. The harness
  performs the authoritative validation.

Reference: <https://build123d.readthedocs.io/>
