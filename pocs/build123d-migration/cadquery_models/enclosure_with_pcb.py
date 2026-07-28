"""Corrected CadQuery comparison model for the PCB enclosure template intent."""

import cadquery as cq


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


def build() -> cq.Workplane:
    outer = (
        cq.Workplane("XY")
        .box(WIDTH, DEPTH, HEIGHT, centered=(True, True, False))
        .edges("|Z")
        .fillet(OUTER_FILLET)
    )
    inner = (
        cq.Workplane("XY", origin=(0.0, 0.0, WALL_THICKNESS))
        .box(
            INTERNAL_WIDTH,
            INTERNAL_DEPTH,
            INTERNAL_HEIGHT + 0.1,
            centered=(True, True, False),
        )
    )
    body = outer.cut(inner)

    for x, y in BOSS_POSITIONS:
        boss = (
            cq.Workplane("XY", origin=(0.0, 0.0, WALL_THICKNESS - 0.1))
            .center(x, y)
            .circle(BOSS_OD / 2.0)
            .extrude(BOSS_HEIGHT + 0.1)
        )
        pilot = (
            cq.Workplane("XY", origin=(0.0, 0.0, WALL_THICKNESS))
            .center(x, y)
            .circle(BOSS_HOLE / 2.0)
            .extrude(BOSS_HEIGHT)
        )
        body = body.union(boss.cut(pilot))

    connector = (
        cq.Workplane("XY")
        .box(
            WALL_THICKNESS + 2.0,
            CONNECTOR_WIDTH,
            CONNECTOR_HEIGHT,
        )
        .translate((WIDTH / 2.0, 0.0, CONNECTOR_Z))
    )
    return body.cut(connector).clean()


result = build()
assert result.val().isValid()
assert len(result.val().Solids()) == 1
