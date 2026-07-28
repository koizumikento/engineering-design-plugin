from build123d import Align, Box, Compound, Cylinder, Pos, Rot


body_width_x = 70.0
body_depth_y = 50.0
body_height_z = 30.0
wall_thickness = 4.0

cavity_width_x = body_width_x - 2.0 * wall_thickness
cavity_depth_y = body_depth_y - 2.0 * wall_thickness
cavity_height_z = body_height_z - wall_thickness
cavity_bottom_z = wall_thickness

side_port_radius = 5.0
side_port_center_y = 0.0
side_port_center_z = 15.0
side_port_tool_start_x = -35.1
side_port_tool_length = 4.2

slot_center_x = 0.0
slot_center_y = 10.0
slot_straight_length = 14.0
slot_width = 6.0
slot_end_radius = slot_width / 2.0
slot_end_offset_x = slot_straight_length / 2.0
slot_height = wall_thickness

lid_width_x = 70.0
lid_depth_y = 50.0
lid_height_z = 4.0
lid_bottom_z = 34.0
lid_top_z = lid_bottom_z + lid_height_z

hole_offset_x = 25.0
hole_offset_y = 15.0
through_hole_radius = 2.0
counterbore_radius = 4.0
counterbore_depth = 2.0
hole_tool_margin = 0.1


body_outer = Box(
    body_width_x,
    body_depth_y,
    body_height_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
cavity = Pos(0, 0, cavity_bottom_z) * Box(
    cavity_width_x,
    cavity_depth_y,
    cavity_height_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
side_port = (
    Pos(side_port_tool_start_x, side_port_center_y, side_port_center_z)
    * Rot(0, 90, 0)
    * Cylinder(
        side_port_radius,
        side_port_tool_length,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
)

slot_middle = Pos(slot_center_x, slot_center_y, 0) * Box(
    slot_straight_length,
    slot_width,
    slot_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
slot_left_end = Pos(
    slot_center_x - slot_end_offset_x, slot_center_y, 0
) * Cylinder(
    slot_end_radius,
    slot_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
slot_right_end = Pos(
    slot_center_x + slot_end_offset_x, slot_center_y, 0
) * Cylinder(
    slot_end_radius,
    slot_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
floor_slot = (slot_middle + slot_left_end + slot_right_end).clean()

body = (body_outer - cavity - side_port - floor_slot).clean()

lid_blank = Pos(0, 0, lid_bottom_z) * Box(
    lid_width_x,
    lid_depth_y,
    lid_height_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

through_hole_start_z = lid_bottom_z - hole_tool_margin
through_hole_height = lid_height_z + 2.0 * hole_tool_margin
counterbore_start_z = lid_top_z - counterbore_depth
counterbore_height = counterbore_depth + hole_tool_margin

lid = lid_blank
for x_position in (-hole_offset_x, hole_offset_x):
    for y_position in (-hole_offset_y, hole_offset_y):
        through_hole = Pos(
            x_position, y_position, through_hole_start_z
        ) * Cylinder(
            through_hole_radius,
            through_hole_height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        counterbore = Pos(
            x_position, y_position, counterbore_start_z
        ) * Cylinder(
            counterbore_radius,
            counterbore_height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        lid = lid - through_hole - counterbore

lid = lid.clean()
result = Compound(children=[body, lid])
