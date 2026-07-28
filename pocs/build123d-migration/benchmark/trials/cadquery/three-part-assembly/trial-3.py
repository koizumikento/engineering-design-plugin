import cadquery as cq


# Assembly datum A0 uses the world origin and identity rotation.
assembly_origin = (0.0, 0.0, 0.0)

# Base plate parameters and local datum B0.
base_length_x = 100.0
base_width_y = 60.0
base_height_z = 6.0
base_hole_diameter = 6.0
base_hole_radius = base_hole_diameter / 2.0
base_hole_centers = [
    (-40.0, -20.0),
    (-40.0, 20.0),
    (40.0, -20.0),
    (40.0, 20.0),
]
base_translation = (0.0, 0.0, 0.0)

base_local = cq.Workplane("XY", origin=assembly_origin).box(
    base_length_x,
    base_width_y,
    base_height_z,
    centered=(True, True, False),
)
base_holes_local = (
    cq.Workplane("XY", origin=assembly_origin)
    .pushPoints(base_hole_centers)
    .circle(base_hole_radius)
    .extrude(base_height_z)
)
base_plate = base_local.cut(base_holes_local).clean().translate(base_translation)

# Spacer ring parameters and local datum S0.
spacer_outer_diameter = 40.0
spacer_inner_diameter = 20.0
spacer_outer_radius = spacer_outer_diameter / 2.0
spacer_inner_radius = spacer_inner_diameter / 2.0
spacer_height_z = 10.0
spacer_translation = (0.0, 0.0, 16.0)

spacer_outer_local = (
    cq.Workplane("XY", origin=assembly_origin)
    .circle(spacer_outer_radius)
    .extrude(spacer_height_z)
)
spacer_inner_local = (
    cq.Workplane("XY", origin=assembly_origin)
    .circle(spacer_inner_radius)
    .extrude(spacer_height_z)
)
spacer_ring = (
    spacer_outer_local.cut(spacer_inner_local).clean().translate(spacer_translation)
)

# Top plate parameters and local datum T0.
top_length_x = 60.0
top_width_y = 40.0
top_height_z = 5.0
top_hole_diameter = 12.0
top_hole_radius = top_hole_diameter / 2.0
top_translation = (0.0, 0.0, 36.0)

top_local = cq.Workplane("XY", origin=assembly_origin).box(
    top_length_x,
    top_width_y,
    top_height_z,
    centered=(True, True, False),
)
top_hole_local = (
    cq.Workplane("XY", origin=assembly_origin)
    .circle(top_hole_radius)
    .extrude(top_height_z)
)
top_plate = top_local.cut(top_hole_local).clean().translate(top_translation)

# Preserve the three components as separate solids.
result = cq.Compound.makeCompound(
    [base_plate.val(), spacer_ring.val(), top_plate.val()]
)
