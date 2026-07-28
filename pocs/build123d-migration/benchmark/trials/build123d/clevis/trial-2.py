from build123d import Align, Box, Cylinder, Pos, Rot


base_size_x = 50.0
part_size_y = 30.0
base_size_z = 10.0

arm_size_x = 10.0
arm_size_z = 40.0
arm_bottom_z = 10.0
left_arm_center_x = -20.0
right_arm_center_x = 20.0

hole_radius = 4.0
hole_length_y = 30.0
hole_start_y = -15.0
hole_center_z = 38.0

base = Box(
    base_size_x,
    part_size_y,
    base_size_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

left_arm = Pos(left_arm_center_x, 0.0, arm_bottom_z) * Box(
    arm_size_x,
    part_size_y,
    arm_size_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
right_arm = Pos(right_arm_center_x, 0.0, arm_bottom_z) * Box(
    arm_size_x,
    part_size_y,
    arm_size_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

left_hole = (
    Pos(left_arm_center_x, hole_start_y, hole_center_z)
    * Rot(-90.0, 0.0, 0.0)
    * Cylinder(
        hole_radius,
        hole_length_y,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
)
right_hole = (
    Pos(right_arm_center_x, hole_start_y, hole_center_z)
    * Rot(-90.0, 0.0, 0.0)
    * Cylinder(
        hole_radius,
        hole_length_y,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
)

result = (base + left_arm + right_arm - left_hole - right_hole).clean()
