from build123d import Align, Box, Cone, Cylinder, Pos


lower_radius = 18.0
lower_height = 12.0

middle_radius = 12.0
middle_z = 12.0
middle_height = 30.0

upper_radius = 8.0
upper_z = 42.0
upper_straight_height = 19.0

chamfer_height = 1.0
chamfer_bottom_radius = 8.0
chamfer_top_radius = 7.0
chamfer_z = 61.0

bore_radius = 3.0
shaft_height = 62.0

keyway_width = 6.0
keyway_radial_span = 11.0
keyway_z = 16.0
keyway_height = 22.0
keyway_center_y = 14.5

centered_on_z_min = (Align.CENTER, Align.CENTER, Align.MIN)

lower_step = Cylinder(
    lower_radius,
    lower_height,
    align=centered_on_z_min,
)
middle_step = Pos(0, 0, middle_z) * Cylinder(
    middle_radius,
    middle_height,
    align=centered_on_z_min,
)
upper_straight = Pos(0, 0, upper_z) * Cylinder(
    upper_radius,
    upper_straight_height,
    align=centered_on_z_min,
)
upper_chamfer = Pos(0, 0, chamfer_z) * Cone(
    chamfer_bottom_radius,
    chamfer_top_radius,
    chamfer_height,
    align=centered_on_z_min,
)

bore = Cylinder(
    bore_radius,
    shaft_height,
    align=centered_on_z_min,
)
keyway = Pos(0, keyway_center_y, keyway_z) * Box(
    keyway_width,
    keyway_radial_span,
    keyway_height,
    align=centered_on_z_min,
)

result = (
    lower_step
    + middle_step
    + upper_straight
    + upper_chamfer
    - bore
    - keyway
).clean()
