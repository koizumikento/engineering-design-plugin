"""Parametric build123d stepped-shaft template."""

from build123d import Align, Box, Cylinder, Pos


SHAFT_SEGMENTS = [
    (20.0, 30.0),
    (15.0, 50.0),
    (10.0, 20.0),
]
BORE_DIAMETER = 3.0
KEYWAY_WIDTH = 5.0
KEYWAY_DEPTH = 2.5
KEYWAY_LENGTH = 40.0

current_z = 0.0
result = None
for diameter, length in SHAFT_SEGMENTS:
    segment = Pos(0, 0, current_z) * Cylinder(
        diameter / 2,
        length,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    result = segment if result is None else result + segment
    current_z += length

result = result.clean()
result -= Cylinder(
    BORE_DIAMETER / 2,
    current_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

middle_start = SHAFT_SEGMENTS[0][1]
middle_radius = SHAFT_SEGMENTS[1][0] / 2
keyway = Pos(
    0,
    middle_radius - KEYWAY_DEPTH,
    middle_start,
) * Box(
    KEYWAY_WIDTH,
    KEYWAY_DEPTH + 1,
    KEYWAY_LENGTH,
    align=(Align.CENTER, Align.MIN, Align.MIN),
)
result = (result - keyway).clean()
result.label = "stepped_shaft"

cad_expectations = {
    "topology": {"solids": 1},
    "bounding_box": {
        "x_len": max(segment[0] for segment in SHAFT_SEGMENTS),
        "y_len": max(segment[0] for segment in SHAFT_SEGMENTS),
        "z_len": sum(segment[1] for segment in SHAFT_SEGMENTS),
    },
}
