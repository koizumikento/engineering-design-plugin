"""Parametric build123d L-bracket template."""

from build123d import Align, Axis, Box, Cylinder, Pos, fillet


WIDTH = 40.0
LEG1_LENGTH = 50.0
LEG2_LENGTH = 60.0
THICKNESS = 5.0
CORNER_FILLET = 8.0
HOLE_DIAMETER = 6.4

align_min = (Align.MIN, Align.MIN, Align.MIN)
horizontal = Box(LEG1_LENGTH, WIDTH, THICKNESS, align=align_min)
vertical = Box(THICKNESS, WIDTH, LEG2_LENGTH, align=align_min)
result = horizontal + vertical

inner_edges = [
    edge
    for edge in result.edges().filter_by(Axis.Y)
    if abs(edge.center().X - THICKNESS) < 1e-6
    and abs(edge.center().Z - THICKNESS) < 1e-6
]
result = fillet(inner_edges, radius=CORNER_FILLET)

base_hole = Pos(25, WIDTH / 2, -1) * Cylinder(
    HOLE_DIAMETER / 2,
    THICKNESS + 2,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
wall_hole = Pos(-1, WIDTH / 2, 30) * Cylinder(
    HOLE_DIAMETER / 2,
    THICKNESS + 2,
    rotation=(0, 90, 0),
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
result = (result - base_hole - wall_hole).clean()
result.label = "l_bracket"

cad_expectations = {"topology": {"solids": 1}}
