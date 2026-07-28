from build123d import Align, Box, Cylinder, Pos


outer_x = 80.0
outer_y = 50.0
outer_z = 30.0

wall_thickness = 3.0
bottom_thickness = 3.0
cavity_x = outer_x - 2.0 * wall_thickness
cavity_y = outer_y - 2.0 * wall_thickness
cavity_z = outer_z - bottom_thickness

standoff_radius = 4.0
standoff_z_min = 3.0
standoff_z_max = 12.0
standoff_height = standoff_z_max - standoff_z_min

blind_hole_radius = 1.5
blind_hole_z_min = 6.0
blind_hole_z_max = 12.0
blind_hole_depth = blind_hole_z_max - blind_hole_z_min

standoff_centers = (
    (-28.0, -13.0),
    (-28.0, 13.0),
    (28.0, -13.0),
    (28.0, 13.0),
)

outer = Box(
    outer_x,
    outer_y,
    outer_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
cavity = Pos(0.0, 0.0, bottom_thickness) * Box(
    cavity_x,
    cavity_y,
    cavity_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

enclosure = outer - cavity

for center_x, center_y in standoff_centers:
    standoff = Pos(center_x, center_y, standoff_z_min) * Cylinder(
        standoff_radius,
        standoff_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    enclosure = enclosure + standoff

for center_x, center_y in standoff_centers:
    blind_hole = Pos(center_x, center_y, blind_hole_z_min) * Cylinder(
        blind_hole_radius,
        blind_hole_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    enclosure = enclosure - blind_hole

result = enclosure.clean()
