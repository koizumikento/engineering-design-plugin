import cadquery as cq


# Assembly datum A0 is the world origin with identity rotation.
BASE_TRANSLATION = (0.0, 0.0, 0.0)
SPACER_TRANSLATION = (0.0, 0.0, 16.0)
TOP_TRANSLATION = (0.0, 0.0, 36.0)

# Base plate in local datum B0.
BASE_WIDTH = 100.0
BASE_DEPTH = 60.0
BASE_THICKNESS = 6.0
BASE_HOLE_DIAMETER = 6.0
BASE_HOLE_RADIUS = BASE_HOLE_DIAMETER / 2.0
BASE_HOLE_CENTERS = [
    (-40.0, -20.0),
    (-40.0, 20.0),
    (40.0, -20.0),
    (40.0, 20.0),
]

base_plate_local = cq.Workplane("XY").box(
    BASE_WIDTH,
    BASE_DEPTH,
    BASE_THICKNESS,
    centered=(True, True, False),
)
base_holes_local = (
    cq.Workplane("XY")
    .pushPoints(BASE_HOLE_CENTERS)
    .circle(BASE_HOLE_RADIUS)
    .extrude(BASE_THICKNESS)
)
base_plate_local = base_plate_local.cut(base_holes_local)
base_plate = base_plate_local.translate(BASE_TRANSLATION)

# Spacer ring in local datum S0.
SPACER_OUTSIDE_DIAMETER = 40.0
SPACER_INSIDE_DIAMETER = 20.0
SPACER_OUTSIDE_RADIUS = SPACER_OUTSIDE_DIAMETER / 2.0
SPACER_INSIDE_RADIUS = SPACER_INSIDE_DIAMETER / 2.0
SPACER_HEIGHT = 10.0

spacer_outer_local = (
    cq.Workplane("XY").circle(SPACER_OUTSIDE_RADIUS).extrude(SPACER_HEIGHT)
)
spacer_bore_local = (
    cq.Workplane("XY").circle(SPACER_INSIDE_RADIUS).extrude(SPACER_HEIGHT)
)
spacer_ring_local = spacer_outer_local.cut(spacer_bore_local)
spacer_ring = spacer_ring_local.translate(SPACER_TRANSLATION)

# Top plate in local datum T0.
TOP_WIDTH = 60.0
TOP_DEPTH = 40.0
TOP_THICKNESS = 5.0
TOP_HOLE_DIAMETER = 12.0
TOP_HOLE_RADIUS = TOP_HOLE_DIAMETER / 2.0

top_plate_local = cq.Workplane("XY").box(
    TOP_WIDTH,
    TOP_DEPTH,
    TOP_THICKNESS,
    centered=(True, True, False),
)
top_hole_local = (
    cq.Workplane("XY").circle(TOP_HOLE_RADIUS).extrude(TOP_THICKNESS)
)
top_plate_local = top_plate_local.cut(top_hole_local)
top_plate = top_plate_local.translate(TOP_TRANSLATION)

# Preserve the three sharp-edged components as separate solids.
result = cq.Compound.makeCompound(
    [
        base_plate.val(),
        spacer_ring.val(),
        top_plate.val(),
    ]
)
