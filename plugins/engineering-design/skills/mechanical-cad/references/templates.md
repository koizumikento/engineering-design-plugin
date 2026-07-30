# build123d patterns

Example dimensions are placeholders. Replace them from the specification,
manufacturer drawing, process capability, and tolerance analysis.

## Parametric plate with hole pattern

```python
from build123d import Align, Box, Cylinder, Pos

PLATE_X, PLATE_Y, PLATE_Z = 80.0, 50.0, 4.0
HOLE_D = 3.4
MOUNT_POINTS = [(-30.0, -15.0), (30.0, -15.0), (-30.0, 15.0), (30.0, 15.0)]

result = Box(
    PLATE_X,
    PLATE_Y,
    PLATE_Z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
for x, y in MOUNT_POINTS:
    result -= Pos(x, y, -1) * Cylinder(
        HOLE_D / 2,
        PLATE_Z + 2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
result = result.clean()
```

## Hollow enclosure body

```python
from build123d import Align, Box, Pos

OUTER_X, OUTER_Y, OUTER_Z = 100.0, 60.0, 35.0
WALL = 2.4

outer = Box(
    OUTER_X,
    OUTER_Y,
    OUTER_Z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
inner = Pos(0, 0, WALL) * Box(
    OUTER_X - 2 * WALL,
    OUTER_Y - 2 * WALL,
    OUTER_Z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
result = (outer - inner).clean()
```

Constructing the cavity explicitly makes the controlling wall and floor
dimensions visible. Add draft, lip, gasket, and snap features only when sourced.

## Named bosses

```python
from build123d import Align, Cylinder, Pos

BOSS_Z, BOSS_OD, PILOT_D = 6.0, 7.0, 2.5
MOUNT_POINTS = [(-22.0, -12.0), (22.0, -12.0), (-22.0, 12.0), (22.0, 12.0)]

bosses = None
for x, y in MOUNT_POINTS:
    boss = Pos(x, y, 0) * Cylinder(
        BOSS_OD / 2,
        BOSS_Z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pilot = Pos(x, y, 0) * Cylinder(
        PILOT_D / 2,
        BOSS_Z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    boss = boss - pilot
    bosses = boss if bosses is None else bosses + boss
```

## Assembly with explicit locations and labels

```python
from build123d import Compound, Pos

base.label = "base"
pcb = Pos(0, 0, pcb_seating_z) * pcb_envelope
pcb.label = "pcb"
lid = Pos(0, 0, lid_seating_z) * lid
lid.label = "lid"
result = Compound(label="device", children=[base, pcb, lid])
```

For datum relationships that should recompute placement, prefer a named
build123d joint as described in `build123d-api.md`.

## Validation

```python
assert result.is_valid
box = result.bounding_box()
assert box.size.X > 0 and box.size.Y > 0 and box.size.Z > 0
assert result.volume > 0
```

Generate standard artifacts with:

```bash
uv run python scripts/cad_runner.py model.py \
  -o outputs/ --report --fail-on-check
```
