"""Corrected CadQuery comparison model for the sensor-enclosure specification."""

import cadquery as cq


WIDTH = 60.0
DEPTH = 40.0
HEIGHT = 25.0
WALL = 2.0
LID_HEIGHT = 5.0
LID_LIP = 2.0
SCREW_HOLE = 3.2
SCREW_CBORE = 6.5
SCREW_CBORE_DEPTH = 3.5
SCREW_OFFSET = 5.0
GLAND_HOLE = 12.5
MOUNT_SLOT_LENGTH = 8.0
MOUNT_SLOT_WIDTH = 5.0
MOUNT_SLOT_SPACING = 30.0
OUTER_FILLET = 3.0

BODY_HEIGHT = HEIGHT - LID_HEIGHT
BOSS_OD = 6.0
BOSS_HEIGHT = BODY_HEIGHT - WALL - 2.0
BOSS_HOLE = 2.5
BOSS_POSITIONS = [
    (WIDTH / 2.0 - SCREW_OFFSET, DEPTH / 2.0 - SCREW_OFFSET),
    (-WIDTH / 2.0 + SCREW_OFFSET, DEPTH / 2.0 - SCREW_OFFSET),
    (WIDTH / 2.0 - SCREW_OFFSET, -DEPTH / 2.0 + SCREW_OFFSET),
    (-WIDTH / 2.0 + SCREW_OFFSET, -DEPTH / 2.0 + SCREW_OFFSET),
]


def build_body() -> cq.Workplane:
    outer = (
        cq.Workplane("XY")
        .box(WIDTH, DEPTH, BODY_HEIGHT, centered=(True, True, False))
        .edges("|Z")
        .fillet(OUTER_FILLET)
    )
    inner = (
        cq.Workplane("XY", origin=(0.0, 0.0, WALL))
        .box(
            WIDTH - 2.0 * WALL,
            DEPTH - 2.0 * WALL,
            BODY_HEIGHT - WALL + 0.1,
            centered=(True, True, False),
        )
    )
    body = outer.cut(inner)

    gland = (
        cq.Workplane("YZ", origin=(-WIDTH / 2.0 - 1.0, 0.0, 0.0))
        .center(0.0, BODY_HEIGHT / 2.0)
        .circle(GLAND_HOLE / 2.0)
        .extrude(WALL + 2.0)
    )
    body = body.cut(gland)

    for x in (-MOUNT_SLOT_SPACING / 2.0, MOUNT_SLOT_SPACING / 2.0):
        slot = (
            cq.Workplane("XY", origin=(0.0, 0.0, -1.0))
            .center(x, 0.0)
            .slot2D(MOUNT_SLOT_LENGTH, MOUNT_SLOT_WIDTH, angle=90.0)
            .extrude(WALL + 2.0)
        )
        body = body.cut(slot)

    for x, y in BOSS_POSITIONS:
        boss = (
            cq.Workplane("XY", origin=(0.0, 0.0, WALL - 0.1))
            .center(x, y)
            .circle(BOSS_OD / 2.0)
            .extrude(BOSS_HEIGHT + 0.1)
        )
        pilot = (
            cq.Workplane("XY", origin=(0.0, 0.0, WALL))
            .center(x, y)
            .circle(BOSS_HOLE / 2.0)
            .extrude(BOSS_HEIGHT)
        )
        body = body.union(boss.cut(pilot))
    return body.clean()


def build_lid() -> cq.Workplane:
    lid = (
        cq.Workplane("XY", origin=(0.0, 0.0, BODY_HEIGHT))
        .box(WIDTH, DEPTH, LID_HEIGHT, centered=(True, True, False))
        .edges("|Z")
        .fillet(OUTER_FILLET)
    )
    lip = (
        cq.Workplane("XY", origin=(0.0, 0.0, BODY_HEIGHT - LID_LIP))
        .box(
            WIDTH - 2.0 * WALL - 0.4,
            DEPTH - 2.0 * WALL - 0.4,
            LID_LIP + 0.1,
            centered=(True, True, False),
        )
    )
    lid = lid.union(lip)

    through_holes = (
        cq.Workplane("XY", origin=(0.0, 0.0, BODY_HEIGHT - 0.1))
        .pushPoints(BOSS_POSITIONS)
        .circle(SCREW_HOLE / 2.0)
        .extrude(LID_HEIGHT + 0.2)
    )
    counterbores = (
        cq.Workplane(
            "XY",
            origin=(0.0, 0.0, HEIGHT - SCREW_CBORE_DEPTH),
        )
        .pushPoints(BOSS_POSITIONS)
        .circle(SCREW_CBORE / 2.0)
        .extrude(SCREW_CBORE_DEPTH + 0.1)
    )
    return lid.cut(through_holes).cut(counterbores).clean()


body = build_body()
lid = build_lid()
result = cq.Compound.makeCompound([body.val(), lid.val()])

assert body.val().isValid()
assert lid.val().isValid()
assert result.isValid()
