from build123d import Align, Box, Compound, Cylinder, Pos


# Assembly datum A0 is the world origin with identity rotation.
BASE_SIZE_X = 100.0
BASE_SIZE_Y = 60.0
BASE_THICKNESS = 6.0
BASE_HOLE_DIAMETER = 6.0
BASE_HOLE_RADIUS = BASE_HOLE_DIAMETER / 2.0
BASE_HOLE_CENTERS = (
    (-40.0, -20.0),
    (-40.0, 20.0),
    (40.0, -20.0),
    (40.0, 20.0),
)
BASE_TRANSLATION = (0.0, 0.0, 0.0)

SPACER_OUTSIDE_DIAMETER = 40.0
SPACER_INSIDE_DIAMETER = 20.0
SPACER_OUTSIDE_RADIUS = SPACER_OUTSIDE_DIAMETER / 2.0
SPACER_INSIDE_RADIUS = SPACER_INSIDE_DIAMETER / 2.0
SPACER_HEIGHT = 10.0
SPACER_TRANSLATION = (0.0, 0.0, 16.0)

TOP_SIZE_X = 60.0
TOP_SIZE_Y = 40.0
TOP_THICKNESS = 5.0
TOP_HOLE_DIAMETER = 12.0
TOP_HOLE_RADIUS = TOP_HOLE_DIAMETER / 2.0
TOP_TRANSLATION = (0.0, 0.0, 36.0)

LOCAL_BOTTOM_ALIGNMENT = (Align.CENTER, Align.CENTER, Align.MIN)


# base_plate in local datum B0, followed by the exact B0-to-A0 transform.
base_plate_local = Box(
    BASE_SIZE_X,
    BASE_SIZE_Y,
    BASE_THICKNESS,
    align=LOCAL_BOTTOM_ALIGNMENT,
)
for hole_x, hole_y in BASE_HOLE_CENTERS:
    base_hole = Pos(hole_x, hole_y, 0.0) * Cylinder(
        BASE_HOLE_RADIUS,
        BASE_THICKNESS,
        align=LOCAL_BOTTOM_ALIGNMENT,
    )
    base_plate_local = base_plate_local - base_hole
base_plate = (Pos(*BASE_TRANSLATION) * base_plate_local.clean()).clean()


# spacer_ring in local datum S0, followed by the exact S0-to-A0 transform.
spacer_outer_local = Cylinder(
    SPACER_OUTSIDE_RADIUS,
    SPACER_HEIGHT,
    align=LOCAL_BOTTOM_ALIGNMENT,
)
spacer_bore_local = Cylinder(
    SPACER_INSIDE_RADIUS,
    SPACER_HEIGHT,
    align=LOCAL_BOTTOM_ALIGNMENT,
)
spacer_ring_local = (spacer_outer_local - spacer_bore_local).clean()
spacer_ring = (Pos(*SPACER_TRANSLATION) * spacer_ring_local).clean()


# top_plate in local datum T0, followed by the exact T0-to-A0 transform.
top_plate_local = Box(
    TOP_SIZE_X,
    TOP_SIZE_Y,
    TOP_THICKNESS,
    align=LOCAL_BOTTOM_ALIGNMENT,
)
top_hole_local = Cylinder(
    TOP_HOLE_RADIUS,
    TOP_THICKNESS,
    align=LOCAL_BOTTOM_ALIGNMENT,
)
top_plate_local = (top_plate_local - top_hole_local).clean()
top_plate = (Pos(*TOP_TRANSLATION) * top_plate_local).clean()


result = Compound(children=[base_plate, spacer_ring, top_plate])
