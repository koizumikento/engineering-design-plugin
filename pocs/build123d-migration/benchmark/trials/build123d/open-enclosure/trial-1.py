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
standoff_bottom_z = 3.0
standoff_top_z = 12.0
standoff_height = standoff_top_z - standoff_bottom_z
standoff_x_positions = (-28.0, 28.0)
standoff_y_positions = (-13.0, 13.0)

hole_radius = 1.5
hole_bottom_z = 6.0
hole_top_z = 12.0
hole_depth = hole_top_z - hole_bottom_z

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

for x_position in standoff_x_positions:
    for y_position in standoff_y_positions:
        standoff = Pos(x_position, y_position, standoff_bottom_z) * Cylinder(
            standoff_radius,
            standoff_height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        enclosure = enclosure + standoff

for x_position in standoff_x_positions:
    for y_position in standoff_y_positions:
        blind_hole = Pos(x_position, y_position, hole_bottom_z) * Cylinder(
            hole_radius,
            hole_depth,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        enclosure = enclosure - blind_hole

result = enclosure.clean()
