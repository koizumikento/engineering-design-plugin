"""Sensor enclosure implemented as a labeled build123d assembly."""

from build123d import Align, Axis, Box, Compound, Cylinder, Pos, fillet


WIDTH = 60.0
DEPTH = 40.0
HEIGHT = 25.0
WALL = 2.0
LID_HEIGHT = 5.0
LID_LIP = 2.0
BODY_HEIGHT = HEIGHT - LID_HEIGHT
SCREW_HOLE = 3.2
SCREW_CBORE = 6.5
SCREW_CBORE_DEPTH = 3.5
SCREW_OFFSET = 5.0
GLAND_HOLE = 12.5
OUTER_FILLET = 3.0

BOSS_POSITIONS = [
    (WIDTH / 2 - SCREW_OFFSET, DEPTH / 2 - SCREW_OFFSET),
    (-WIDTH / 2 + SCREW_OFFSET, DEPTH / 2 - SCREW_OFFSET),
    (WIDTH / 2 - SCREW_OFFSET, -DEPTH / 2 + SCREW_OFFSET),
    (-WIDTH / 2 + SCREW_OFFSET, -DEPTH / 2 + SCREW_OFFSET),
]

outer = Box(
    WIDTH,
    DEPTH,
    BODY_HEIGHT,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
outer = fillet(outer.edges().filter_by(Axis.Z), radius=OUTER_FILLET)
inner = Pos(0, 0, WALL) * Box(
    WIDTH - 2 * WALL,
    DEPTH - 2 * WALL,
    BODY_HEIGHT,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
body = outer - inner

gland = Pos(-WIDTH / 2 - 1, 0, BODY_HEIGHT / 2) * Cylinder(
    GLAND_HOLE / 2,
    WALL + 2,
    rotation=(0, 90, 0),
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
body -= gland

for x, y in BOSS_POSITIONS:
    boss = Pos(x, y, WALL) * Cylinder(
        3.0,
        BODY_HEIGHT - WALL - 2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    pilot = Pos(x, y, WALL) * Cylinder(
        1.25,
        BODY_HEIGHT - WALL - 2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body += boss - pilot
body = body.clean()
body.label = "body"

lid = Pos(0, 0, BODY_HEIGHT) * Box(
    WIDTH,
    DEPTH,
    LID_HEIGHT,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
lid = fillet(lid.edges().filter_by(Axis.Z), radius=OUTER_FILLET)
lip = Pos(0, 0, BODY_HEIGHT - LID_LIP) * Box(
    WIDTH - 2 * WALL - 0.4,
    DEPTH - 2 * WALL - 0.4,
    LID_LIP,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
lid += lip

for x, y in BOSS_POSITIONS:
    lid -= Pos(x, y, BODY_HEIGHT - 0.1) * Cylinder(
        SCREW_HOLE / 2,
        LID_HEIGHT + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    lid -= Pos(x, y, HEIGHT - SCREW_CBORE_DEPTH) * Cylinder(
        SCREW_CBORE / 2,
        SCREW_CBORE_DEPTH + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
lid = lid.clean()
lid.label = "lid"

result = Compound(label="sensor_enclosure", children=[body, lid])
cad_metadata = {
    "units": "mm",
    "kind": "assembly",
    "relationships": [{"type": "static", "fixed": "body", "moving": "lid"}],
}
cad_expectations = {
    "tolerance_mm": 1e-6,
    "topology": {"solids": 2},
    "bounding_box": {"x_len": WIDTH, "y_len": DEPTH, "z_len": HEIGHT},
    "components": {
        "body": {"bounding_box": {"z_min": 0.0, "z_max": BODY_HEIGHT}},
        "lid": {"bounding_box": {"z_min": BODY_HEIGHT - LID_LIP, "z_max": HEIGHT}},
    },
}

assert result.is_valid
