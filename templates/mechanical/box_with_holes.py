"""Parametric build123d box with a four-hole pattern."""

from build123d import Align, Box, Cylinder, Pos


WIDTH = 100.0
DEPTH = 60.0
HEIGHT = 20.0
HOLE_DIAMETER = 5.0
HOLE_OFFSET_X = 40.0
HOLE_OFFSET_Y = 20.0

result = Box(
    WIDTH,
    DEPTH,
    HEIGHT,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
for x in (-HOLE_OFFSET_X, HOLE_OFFSET_X):
    for y in (-HOLE_OFFSET_Y, HOLE_OFFSET_Y):
        result -= Pos(x, y, -1) * Cylinder(
            HOLE_DIAMETER / 2,
            HEIGHT + 2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
result = result.clean()
result.label = "box_with_holes"

cad_expectations = {
    "topology": {"solids": 1},
    "bounding_box": {"x_len": WIDTH, "y_len": DEPTH, "z_len": HEIGHT},
}
