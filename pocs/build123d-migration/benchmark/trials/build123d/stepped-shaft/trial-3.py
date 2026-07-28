from build123d import Align, Box, Cone, Cylinder, Pos


LOWER_DIAMETER = 36.0
LOWER_HEIGHT = 12.0

MIDDLE_DIAMETER = 24.0
MIDDLE_Z_MIN = 12.0
MIDDLE_HEIGHT = 30.0

UPPER_DIAMETER = 16.0
UPPER_Z_MIN = 42.0
UPPER_STRAIGHT_HEIGHT = 19.0

CHAMFER_HEIGHT = 1.0
CHAMFER_RADIAL_SIZE = 1.0

BORE_DIAMETER = 6.0
SHAFT_HEIGHT = 62.0

KEYWAY_WIDTH = 6.0
KEYWAY_Y_MIN = 9.0
KEYWAY_Y_MAX = 20.0
KEYWAY_Z_MIN = 16.0
KEYWAY_Z_MAX = 38.0

centered_min_z = (Align.CENTER, Align.CENTER, Align.MIN)
center_x_min_yz = (Align.CENTER, Align.MIN, Align.MIN)

lower_step = Cylinder(
    LOWER_DIAMETER / 2.0,
    LOWER_HEIGHT,
    align=centered_min_z,
)
middle_step = Pos(0, 0, MIDDLE_Z_MIN) * Cylinder(
    MIDDLE_DIAMETER / 2.0,
    MIDDLE_HEIGHT,
    align=centered_min_z,
)
upper_step = Pos(0, 0, UPPER_Z_MIN) * Cylinder(
    UPPER_DIAMETER / 2.0,
    UPPER_STRAIGHT_HEIGHT,
    align=centered_min_z,
)
top_chamfer = Pos(0, 0, UPPER_Z_MIN + UPPER_STRAIGHT_HEIGHT) * Cone(
    UPPER_DIAMETER / 2.0,
    UPPER_DIAMETER / 2.0 - CHAMFER_RADIAL_SIZE,
    CHAMFER_HEIGHT,
    align=centered_min_z,
)

bore = Cylinder(
    BORE_DIAMETER / 2.0,
    SHAFT_HEIGHT,
    align=centered_min_z,
)
keyway = Pos(0, KEYWAY_Y_MIN, KEYWAY_Z_MIN) * Box(
    KEYWAY_WIDTH,
    KEYWAY_Y_MAX - KEYWAY_Y_MIN,
    KEYWAY_Z_MAX - KEYWAY_Z_MIN,
    align=center_x_min_yz,
)

result = (
    (lower_step + middle_step + upper_step + top_chamfer) - bore - keyway
).clean()
