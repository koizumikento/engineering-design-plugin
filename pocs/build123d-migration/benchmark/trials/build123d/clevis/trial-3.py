from build123d import Align, Box, Cylinder, Pos, Rot


base_x = 50
base_y = 30
base_z = 10

arm_x = 10
arm_y = 30
arm_z = 40
arm_center_x = 20
arm_bottom_z = 10

hole_radius = 4
hole_length = 30
hole_center_z = 38
hole_start_y = 15

center_min = (Align.CENTER, Align.CENTER, Align.MIN)

base = Box(base_x, base_y, base_z, align=center_min)
left_arm = Pos(-arm_center_x, 0, arm_bottom_z) * Box(
    arm_x, arm_y, arm_z, align=center_min
)
right_arm = Pos(arm_center_x, 0, arm_bottom_z) * Box(
    arm_x, arm_y, arm_z, align=center_min
)

left_hole = Pos(-arm_center_x, hole_start_y, hole_center_z) * (
    Rot(90, 0, 0)
    * Cylinder(hole_radius, hole_length, align=center_min)
)
right_hole = Pos(arm_center_x, hole_start_y, hole_center_z) * (
    Rot(90, 0, 0)
    * Cylinder(hole_radius, hole_length, align=center_min)
)

result = (
    base + left_arm + right_arm - left_hole - right_hole
).clean()
