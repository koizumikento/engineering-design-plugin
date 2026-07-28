from build123d import Align, Box, Cylinder, Pos, Rot


base_width = 50.0
base_depth = 30.0
base_height = 10.0

arm_width = 10.0
arm_depth = 30.0
arm_height = 40.0
arm_center_x = 20.0
arm_bottom_z = 10.0

hole_diameter = 8.0
hole_radius = hole_diameter / 2.0
hole_center_z = 38.0

base = Box(
    base_width,
    base_depth,
    base_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

left_arm = Pos(-arm_center_x, 0, arm_bottom_z) * Box(
    arm_width,
    arm_depth,
    arm_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
right_arm = Pos(arm_center_x, 0, arm_bottom_z) * Box(
    arm_width,
    arm_depth,
    arm_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

hole_tool = Rot(90, 0, 0) * Cylinder(
    hole_radius,
    arm_depth,
    align=(Align.CENTER, Align.CENTER, Align.CENTER),
)
left_hole = Pos(-arm_center_x, 0, hole_center_z) * hole_tool
right_hole = Pos(arm_center_x, 0, hole_center_z) * hole_tool

result = (base + left_arm + right_arm - left_hole - right_hole).clean()
