"""CadQuery comparison model for the calibration-block specification."""

import cadquery as cq


WIDTH = 40.0
DEPTH = 30.0
HEIGHT = 12.0
HOLE_DIAMETER = 3.4
HOLE_X = 12.0
POCKET_WIDTH = 20.0
POCKET_DEPTH = 10.0
POCKET_CUT_DEPTH = 2.0
OUTER_FILLET = 1.0


def build() -> cq.Workplane:
    block = (
        cq.Workplane("XY")
        .box(WIDTH, DEPTH, HEIGHT, centered=(True, True, False))
        .edges("|Z")
        .fillet(OUTER_FILLET)
    )
    holes = (
        cq.Workplane("XY")
        .pushPoints([(-HOLE_X, 0.0), (HOLE_X, 0.0)])
        .circle(HOLE_DIAMETER / 2.0)
        .extrude(HEIGHT)
    )
    pocket = (
        cq.Workplane("XY", origin=(0.0, 0.0, HEIGHT - POCKET_CUT_DEPTH))
        .rect(POCKET_WIDTH, POCKET_DEPTH)
        .extrude(POCKET_CUT_DEPTH)
    )
    return block.cut(holes).cut(pocket).clean()


result = build()
assert result.val().isValid()
