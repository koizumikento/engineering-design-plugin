import cadquery as cq


# Assembly datum A0: world origin, identity rotation.
# Base plate parameters and local datum B0.
base_width = 100.0
base_depth = 60.0
base_height = 6.0
base_hole_diameter = 6.0
base_hole_radius = base_hole_diameter / 2.0
base_hole_centers = [
    (-40.0, -20.0),
    (-40.0, 20.0),
    (40.0, -20.0),
    (40.0, 20.0),
]
base_translation = (0.0, 0.0, 0.0)

base_blank = cq.Workplane("XY").box(
    base_width,
    base_depth,
    base_height,
    centered=(True, True, False),
)
base_holes = (
    cq.Workplane("XY")
    .pushPoints(base_hole_centers)
    .circle(base_hole_radius)
    .extrude(base_height)
)
base_plate = base_blank.cut(base_holes).clean().translate(base_translation)


# Spacer ring parameters and local datum S0.
spacer_outer_diameter = 40.0
spacer_inner_diameter = 20.0
spacer_outer_radius = spacer_outer_diameter / 2.0
spacer_inner_radius = spacer_inner_diameter / 2.0
spacer_height = 10.0
spacer_translation = (0.0, 0.0, 16.0)

spacer_outer = cq.Workplane("XY").circle(spacer_outer_radius).extrude(spacer_height)
spacer_bore = cq.Workplane("XY").circle(spacer_inner_radius).extrude(spacer_height)
spacer_ring = spacer_outer.cut(spacer_bore).clean().translate(spacer_translation)


# Top plate parameters and local datum T0.
top_width = 60.0
top_depth = 40.0
top_height = 5.0
top_hole_diameter = 12.0
top_hole_radius = top_hole_diameter / 2.0
top_translation = (0.0, 0.0, 36.0)

top_blank = cq.Workplane("XY").box(
    top_width,
    top_depth,
    top_height,
    centered=(True, True, False),
)
top_bore = cq.Workplane("XY").circle(top_hole_radius).extrude(top_height)
top_plate = top_blank.cut(top_bore).clean().translate(top_translation)


# Preserve all three assembly components as separate solids.
result = cq.Compound.makeCompound(
    [
        base_plate.val(),
        spacer_ring.val(),
        top_plate.val(),
    ]
)
