"""build123d candidate model for the sensor-enclosure specification."""

from build123d import (
    Align,
    Axis,
    Box,
    BuildSketch,
    Compound,
    Cylinder,
    Locations,
    Part,
    Plane,
    Pos,
    SlotOverall,
    extrude,
    fillet,
)


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


def build_body() -> Part:
    outer = Box(
        WIDTH,
        DEPTH,
        BODY_HEIGHT,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    outer = fillet(outer.edges().filter_by(Axis.Z), radius=OUTER_FILLET)
    inner = (
        Pos(0.0, 0.0, WALL)
        * Box(
            WIDTH - 2.0 * WALL,
            DEPTH - 2.0 * WALL,
            BODY_HEIGHT - WALL + 0.1,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )
    body = outer - inner

    gland = (
        Pos(-WIDTH / 2.0, 0.0, BODY_HEIGHT / 2.0)
        * Cylinder(
            GLAND_HOLE / 2.0,
            WALL + 2.0,
            rotation=(0.0, 90.0, 0.0),
        )
    )
    body = body - gland

    slot_plane = Plane.XY.offset(-1.0)
    with BuildSketch(slot_plane) as slot_sketch:
        with Locations(
            (-MOUNT_SLOT_SPACING / 2.0, 0.0),
            (MOUNT_SLOT_SPACING / 2.0, 0.0),
        ):
            SlotOverall(
                MOUNT_SLOT_LENGTH,
                MOUNT_SLOT_WIDTH,
                rotation=90.0,
            )
    slot_tool = extrude(slot_sketch.sketch, amount=WALL + 2.0)
    body = body - slot_tool

    for x, y in BOSS_POSITIONS:
        boss = (
            Pos(x, y, WALL - 0.1)
            * Cylinder(
                BOSS_OD / 2.0,
                BOSS_HEIGHT + 0.1,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        )
        pilot = (
            Pos(x, y, WALL)
            * Cylinder(
                BOSS_HOLE / 2.0,
                BOSS_HEIGHT,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        )
        body = body + (boss - pilot)
    return body.clean()


def build_lid() -> Part:
    lid = (
        Pos(0.0, 0.0, BODY_HEIGHT)
        * Box(
            WIDTH,
            DEPTH,
            LID_HEIGHT,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )
    lid = fillet(lid.edges().filter_by(Axis.Z), radius=OUTER_FILLET)
    lip = (
        Pos(0.0, 0.0, BODY_HEIGHT - LID_LIP)
        * Box(
            WIDTH - 2.0 * WALL - 0.4,
            DEPTH - 2.0 * WALL - 0.4,
            LID_LIP + 0.1,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )
    lid = lid + lip

    for x, y in BOSS_POSITIONS:
        through_hole = (
            Pos(x, y, BODY_HEIGHT + LID_HEIGHT / 2.0)
            * Cylinder(SCREW_HOLE / 2.0, LID_HEIGHT + 0.2)
        )
        counterbore = (
            Pos(x, y, HEIGHT - SCREW_CBORE_DEPTH / 2.0)
            * Cylinder(SCREW_CBORE / 2.0, SCREW_CBORE_DEPTH + 0.1)
        )
        lid = lid - through_hole - counterbore
    return lid.clean()


body = build_body()
lid = build_lid()
body.label = "body"
lid.label = "lid"
result = Compound(children=[body, lid], label="sensor_enclosure")

assert body.is_valid
assert lid.is_valid
