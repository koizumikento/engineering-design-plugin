import cadquery as cq


plate_length = 70.0
plate_width = 40.0
plate_thickness = 8.0

preserved_hole_diameter = 6.0
preserved_hole_centres = [
    (-25.0, -12.0),
    (-25.0, 12.0),
    (25.0, -12.0),
]

pocket_length = 16.0
pocket_width = 6.0
pocket_depth = 2.0
pocket_centre_x = 0.0
pocket_centre_y = -12.0
pocket_bottom_z = 6.0

new_hole_diameter = 10.0
new_hole_centre_x = 15.0
new_hole_centre_y = 8.0

boss_diameter = 16.0
boss_height = 5.0
boss_bottom_z = plate_thickness

bore_diameter = 6.0
bore_height = plate_thickness + boss_height

plate = cq.Workplane("XY").box(
    plate_length,
    plate_width,
    plate_thickness,
    centered=(True, True, False),
)

boss = (
    cq.Workplane("XY", origin=(0.0, 0.0, boss_bottom_z))
    .circle(boss_diameter / 2.0)
    .extrude(boss_height)
)

preserved_holes = (
    cq.Workplane("XY")
    .pushPoints(preserved_hole_centres)
    .circle(preserved_hole_diameter / 2.0)
    .extrude(plate_thickness)
)

pocket = (
    cq.Workplane(
        "XY",
        origin=(pocket_centre_x, pocket_centre_y, pocket_bottom_z),
    )
    .box(
        pocket_length,
        pocket_width,
        pocket_depth,
        centered=(True, True, False),
    )
)

new_hole = (
    cq.Workplane(
        "XY",
        origin=(new_hole_centre_x, new_hole_centre_y, 0.0),
    )
    .circle(new_hole_diameter / 2.0)
    .extrude(plate_thickness)
)

bore = (
    cq.Workplane("XY")
    .circle(bore_diameter / 2.0)
    .extrude(bore_height)
)

result = (
    plate
    .union(boss)
    .cut(preserved_holes)
    .cut(pocket)
    .cut(new_hole)
    .cut(bore)
    .clean()
)
