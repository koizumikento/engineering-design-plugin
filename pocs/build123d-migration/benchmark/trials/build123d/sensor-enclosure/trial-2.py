from build123d import Align, Box, Compound, Cylinder, Pos, Rot


BODY_X = 70.0
BODY_Y = 50.0
BODY_Z = 30.0
WALL = 4.0

CAVITY_X = BODY_X - 2.0 * WALL
CAVITY_Y = BODY_Y - 2.0 * WALL
CAVITY_Z = BODY_Z - WALL

PORT_DIAMETER = 10.0
PORT_RADIUS = PORT_DIAMETER / 2.0
PORT_LENGTH = WALL
PORT_Y = 0.0
PORT_Z = 15.0

SLOT_OVERALL_LENGTH = 20.0
SLOT_WIDTH = 6.0
SLOT_RADIUS = SLOT_WIDTH / 2.0
SLOT_STRAIGHT_LENGTH = SLOT_OVERALL_LENGTH - SLOT_WIDTH
SLOT_CENTER_Y = 10.0
SLOT_Z = 0.0
SLOT_HEIGHT = WALL

LID_X = 70.0
LID_Y = 50.0
LID_Z = 4.0
LID_BOTTOM_Z = 34.0

HOLE_RADIUS = 2.0
HOLE_HEIGHT = LID_Z
COUNTERBORE_RADIUS = 4.0
COUNTERBORE_DEPTH = 2.0
COUNTERBORE_BOTTOM_Z = LID_BOTTOM_Z + LID_Z - COUNTERBORE_DEPTH
HOLE_X_POSITIONS = (-25.0, 25.0)
HOLE_Y_POSITIONS = (-15.0, 15.0)


body_outer = Box(
    BODY_X,
    BODY_Y,
    BODY_Z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
cavity = Pos(0.0, 0.0, WALL) * Box(
    CAVITY_X,
    CAVITY_Y,
    CAVITY_Z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
body = body_outer - cavity

side_port = (
    Pos(-BODY_X / 2.0, PORT_Y, PORT_Z)
    * Rot(0.0, 90.0, 0.0)
    * Cylinder(
        PORT_RADIUS,
        PORT_LENGTH,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
)
body = body - side_port

slot_tool = Pos(0.0, SLOT_CENTER_Y, SLOT_Z) * Box(
    SLOT_STRAIGHT_LENGTH,
    SLOT_WIDTH,
    SLOT_HEIGHT,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
for slot_end_x in (-SLOT_STRAIGHT_LENGTH / 2.0, SLOT_STRAIGHT_LENGTH / 2.0):
    slot_tool = slot_tool + Pos(slot_end_x, SLOT_CENTER_Y, SLOT_Z) * Cylinder(
        SLOT_RADIUS,
        SLOT_HEIGHT,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
body = (body - slot_tool).clean()

lid = Pos(0.0, 0.0, LID_BOTTOM_Z) * Box(
    LID_X,
    LID_Y,
    LID_Z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
for hole_x in HOLE_X_POSITIONS:
    for hole_y in HOLE_Y_POSITIONS:
        through_hole = Pos(hole_x, hole_y, LID_BOTTOM_Z) * Cylinder(
            HOLE_RADIUS,
            HOLE_HEIGHT,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        counterbore = Pos(hole_x, hole_y, COUNTERBORE_BOTTOM_Z) * Cylinder(
            COUNTERBORE_RADIUS,
            COUNTERBORE_DEPTH,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        lid = lid - through_hole - counterbore
lid = lid.clean()

result = Compound(children=[body, lid])
