import cadquery as cq


BLOCK_X = 50.0
BLOCK_Y = 40.0
BLOCK_Z = 20.0
CORNER_RADIUS = 3.0

HOLE_DIAMETER = 5.0
HOLE_CENTERS = [
    (-15.0, -10.0),
    (-15.0, 10.0),
    (15.0, -10.0),
    (15.0, 10.0),
]

POCKET_X = 20.0
POCKET_Y = 12.0
POCKET_DEPTH = 4.0


block = (
    cq.Workplane("XY")
    .box(BLOCK_X, BLOCK_Y, BLOCK_Z, centered=(True, True, False))
    .edges("|Z")
    .fillet(CORNER_RADIUS)
)

through_holes = (
    cq.Workplane("XY", origin=(0.0, 0.0, 0.0))
    .pushPoints(HOLE_CENTERS)
    .circle(HOLE_DIAMETER / 2.0)
    .extrude(BLOCK_Z)
)

top_pocket = (
    cq.Workplane(
        "XY",
        origin=(0.0, 0.0, BLOCK_Z - POCKET_DEPTH),
    )
    .rect(POCKET_X, POCKET_Y)
    .extrude(POCKET_DEPTH)
)

result = block.cut(through_holes).cut(top_pocket).clean()
