"""build123d candidate model for the calibration-block specification."""

from build123d import Align, Axis, Box, Cylinder, Pos, Part, fillet


WIDTH = 40.0
DEPTH = 30.0
HEIGHT = 12.0
HOLE_DIAMETER = 3.4
HOLE_X = 12.0
POCKET_WIDTH = 20.0
POCKET_DEPTH = 10.0
POCKET_CUT_DEPTH = 2.0
OUTER_FILLET = 1.0


def build() -> Part:
    block = Box(
        WIDTH,
        DEPTH,
        HEIGHT,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    block = fillet(block.edges().filter_by(Axis.Z), radius=OUTER_FILLET)

    hole_tool = (
        Pos(-HOLE_X, 0.0, HEIGHT / 2.0)
        * Cylinder(HOLE_DIAMETER / 2.0, HEIGHT + 2.0)
    )
    hole_tool += (
        Pos(HOLE_X, 0.0, HEIGHT / 2.0)
        * Cylinder(HOLE_DIAMETER / 2.0, HEIGHT + 2.0)
    )
    pocket_tool = (
        Pos(0.0, 0.0, HEIGHT - POCKET_CUT_DEPTH / 2.0)
        * Box(POCKET_WIDTH, POCKET_DEPTH, POCKET_CUT_DEPTH)
    )
    return (block - hole_tool - pocket_tool).clean()


result = build()
assert result.is_valid
