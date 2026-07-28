from build123d import Align, Box, Cylinder, Pos


# All dimensions are nominal millimetres.
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
standoff_centres = (
    (-28.0, -13.0),
    (-28.0, 13.0),
    (28.0, -13.0),
    (28.0, 13.0),
)

blind_hole_radius = 1.5
blind_hole_z_min = 6.0
blind_hole_z_max = 12.0
blind_hole_depth = blind_hole_z_max - blind_hole_z_min

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

result = outer - cavity

for centre_x, centre_y in standoff_centres:
    standoff = Pos(centre_x, centre_y, standoff_z_min) * Cylinder(
        standoff_radius,
        standoff_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    result = result + standoff

for centre_x, centre_y in standoff_centres:
    blind_hole = Pos(centre_x, centre_y, blind_hole_z_min) * Cylinder(
        blind_hole_radius,
        blind_hole_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    result = result - blind_hole

result = result.clean()
