import cadquery as cq


# Plate and revision dimensions (mm)
plate_length = 70.0
plate_width = 40.0
plate_thickness = 8.0

preserved_hole_diameter = 6.0
preserved_hole_centres = [(-25.0, -12.0), (-25.0, 12.0), (25.0, -12.0)]

pocket_length = 16.0
pocket_width = 6.0
pocket_depth = 2.0
pocket_centre = (0.0, -12.0)

relocated_hole_diameter = 10.0
relocated_hole_centre = (15.0, 8.0)

boss_diameter = 16.0
boss_height = 5.0
bore_diameter = 6.0

# Build the plate and fuse the centred boss.
plate = cq.Workplane("XY").box(
    plate_length,
    plate_width,
    plate_thickness,
    centered=(True, True, False),
)
boss = (
    cq.Workplane("XY", origin=(0.0, 0.0, plate_thickness))
    .circle(boss_diameter / 2.0)
    .extrude(boss_height)
)
revised_body = plate.union(boss)

# Preserve the three non-target through-holes.
preserved_holes = (
    cq.Workplane("XY")
    .pushPoints(preserved_hole_centres)
    .circle(preserved_hole_diameter / 2.0)
    .extrude(plate_thickness)
)
revised_body = revised_body.cut(preserved_holes)

# Preserve the original blind rectangular pocket exactly.
pocket = (
    cq.Workplane(
        "XY",
        origin=(
            pocket_centre[0],
            pocket_centre[1],
            plate_thickness - pocket_depth,
        ),
    )
    .rect(pocket_length, pocket_width)
    .extrude(pocket_depth)
)
revised_body = revised_body.cut(pocket)

# Add the relocated plate-through hole.
relocated_hole = (
    cq.Workplane(
        "XY",
        origin=(relocated_hole_centre[0], relocated_hole_centre[1], 0.0),
    )
    .circle(relocated_hole_diameter / 2.0)
    .extrude(plate_thickness)
)
revised_body = revised_body.cut(relocated_hole)

# Bore concentrically through the full plate-and-boss height.
overall_height = plate_thickness + boss_height
central_bore = (
    cq.Workplane("XY")
    .circle(bore_diameter / 2.0)
    .extrude(overall_height)
)

result = revised_body.cut(central_bore).clean()
