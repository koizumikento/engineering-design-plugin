from build123d import Align, Box, Compound, Cylinder, Pos, Rot


body_length = 70.0
body_width = 50.0
body_height = 30.0
wall_thickness = 4.0

cavity_length = body_length - 2.0 * wall_thickness
cavity_width = body_width - 2.0 * wall_thickness
cavity_height = body_height - wall_thickness

port_diameter = 10.0
port_length = wall_thickness
port_y = 0.0
port_z = 15.0

slot_overall_length = 20.0
slot_width = 6.0
slot_straight_length = slot_overall_length - slot_width
slot_radius = slot_width / 2.0
slot_center_y = 10.0
slot_end_x = slot_straight_length / 2.0

lid_length = 70.0
lid_width = 50.0
lid_thickness = 4.0
lid_bottom_z = 34.0
through_hole_diameter = 4.0
counterbore_diameter = 8.0
counterbore_depth = 2.0
hole_x_positions = (-25.0, 25.0)
hole_y_positions = (-15.0, 15.0)

body_outer = Box(
    body_length,
    body_width,
    body_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
cavity = Pos(0.0, 0.0, wall_thickness) * Box(
    cavity_length,
    cavity_width,
    cavity_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
side_port = (
    Pos(-body_length / 2.0, port_y, port_z)
    * Rot(0.0, 90.0, 0.0)
    * Cylinder(
        port_diameter / 2.0,
        port_length,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
)

slot_middle = Pos(0.0, slot_center_y, 0.0) * Box(
    slot_straight_length,
    slot_width,
    wall_thickness,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
slot_left_end = Pos(-slot_end_x, slot_center_y, 0.0) * Cylinder(
    slot_radius,
    wall_thickness,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
slot_right_end = Pos(slot_end_x, slot_center_y, 0.0) * Cylinder(
    slot_radius,
    wall_thickness,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
floor_slot = (slot_middle + slot_left_end + slot_right_end).clean()

body = (body_outer - cavity - side_port - floor_slot).clean()

lid = Pos(0.0, 0.0, lid_bottom_z) * Box(
    lid_length,
    lid_width,
    lid_thickness,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
for hole_x in hole_x_positions:
    for hole_y in hole_y_positions:
        through_hole = Pos(hole_x, hole_y, lid_bottom_z) * Cylinder(
            through_hole_diameter / 2.0,
            lid_thickness,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        counterbore = Pos(
            hole_x,
            hole_y,
            lid_bottom_z + lid_thickness - counterbore_depth,
        ) * Cylinder(
            counterbore_diameter / 2.0,
            counterbore_depth,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        lid = lid - through_hole - counterbore

lid = lid.clean()
result = Compound(children=[body, lid])
