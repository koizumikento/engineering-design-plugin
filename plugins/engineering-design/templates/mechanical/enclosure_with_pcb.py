"""Parametric build123d PCB enclosure template."""

from build123d import Align, Box, Cylinder, Pos


PCB_WIDTH = 50.0
PCB_DEPTH = 30.0
PCB_CLEARANCE = 2.0
WALL = 2.0
INTERNAL_HEIGHT = 20.0
BOSS_HEIGHT = 5.0
BOSS_OD = 5.0
BOSS_HOLE = 2.1

INNER_X = PCB_WIDTH + 2 * PCB_CLEARANCE
INNER_Y = PCB_DEPTH + 2 * PCB_CLEARANCE
OUTER_X = INNER_X + 2 * WALL
OUTER_Y = INNER_Y + 2 * WALL
OUTER_Z = INTERNAL_HEIGHT + WALL

outer = Box(
    OUTER_X,
    OUTER_Y,
    OUTER_Z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
inner = Pos(0, 0, WALL) * Box(
    INNER_X,
    INNER_Y,
    INTERNAL_HEIGHT + 1,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
result = outer - inner

for x in (-PCB_WIDTH / 2 + 3, PCB_WIDTH / 2 - 3):
    for y in (-PCB_DEPTH / 2 + 3, PCB_DEPTH / 2 - 3):
        boss = Pos(x, y, WALL) * Cylinder(
            BOSS_OD / 2,
            BOSS_HEIGHT,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        pilot = Pos(x, y, WALL) * Cylinder(
            BOSS_HOLE / 2,
            BOSS_HEIGHT,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        result += boss - pilot

result = result.clean()
result.label = "pcb_enclosure"
cad_expectations = {
    "topology": {"solids": 1},
    "bounding_box": {"x_len": OUTER_X, "y_len": OUTER_Y, "z_len": OUTER_Z},
}
