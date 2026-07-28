"""build123d candidate model for the PCB enclosure template intent."""

from build123d import Align, Axis, Box, Cylinder, Part, Pos, fillet


PCB_WIDTH = 50.0
PCB_DEPTH = 30.0
PCB_THICKNESS = 1.6
PCB_CLEARANCE = 2.0
WALL_THICKNESS = 2.0
INTERNAL_HEIGHT = 20.0
BOSS_HEIGHT = 5.0
BOSS_OD = 5.0
BOSS_HOLE = 2.1
PCB_HOLE_OFFSET = 3.0
CONNECTOR_WIDTH = 10.0
CONNECTOR_HEIGHT = 4.0
OUTER_FILLET = 3.0

INTERNAL_WIDTH = PCB_WIDTH + 2.0 * PCB_CLEARANCE
INTERNAL_DEPTH = PCB_DEPTH + 2.0 * PCB_CLEARANCE
WIDTH = INTERNAL_WIDTH + 2.0 * WALL_THICKNESS
DEPTH = INTERNAL_DEPTH + 2.0 * WALL_THICKNESS
HEIGHT = INTERNAL_HEIGHT + WALL_THICKNESS
CONNECTOR_Z = (
    WALL_THICKNESS + BOSS_HEIGHT + PCB_THICKNESS + CONNECTOR_HEIGHT / 2.0
)
BOSS_X = PCB_WIDTH / 2.0 - PCB_HOLE_OFFSET
BOSS_Y = PCB_DEPTH / 2.0 - PCB_HOLE_OFFSET
BOSS_POSITIONS = [
    (BOSS_X, BOSS_Y),
    (-BOSS_X, BOSS_Y),
    (BOSS_X, -BOSS_Y),
    (-BOSS_X, -BOSS_Y),
]


def build() -> Part:
    outer = Box(
        WIDTH,
        DEPTH,
        HEIGHT,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    outer = fillet(outer.edges().filter_by(Axis.Z), radius=OUTER_FILLET)
    inner = (
        Pos(0.0, 0.0, WALL_THICKNESS)
        * Box(
            INTERNAL_WIDTH,
            INTERNAL_DEPTH,
            INTERNAL_HEIGHT + 0.1,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )
    body = outer - inner

    for x, y in BOSS_POSITIONS:
        boss = (
            Pos(x, y, WALL_THICKNESS - 0.1)
            * Cylinder(
                BOSS_OD / 2.0,
                BOSS_HEIGHT + 0.1,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        )
        pilot = (
            Pos(x, y, WALL_THICKNESS)
            * Cylinder(
                BOSS_HOLE / 2.0,
                BOSS_HEIGHT,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        )
        body = body + (boss - pilot)

    connector = (
        Pos(WIDTH / 2.0, 0.0, CONNECTOR_Z)
        * Box(WALL_THICKNESS + 2.0, CONNECTOR_WIDTH, CONNECTOR_HEIGHT)
    )
    return (body - connector).clean()


result = build()
assert result.is_valid
assert len(result.solids()) == 1
