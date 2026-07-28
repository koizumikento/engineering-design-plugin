import cadquery as cq


base_length_x = 50.0
base_width_y = 30.0
base_height_z = 10.0

arm_width_x = 10.0
arm_depth_y = 30.0
arm_height_z = 40.0
arm_center_x = 20.0
arm_bottom_z = 10.0

hole_radius = 4.0
hole_center_z = 38.0
hole_start_y = 15.0
hole_length_y = 30.0

base = cq.Workplane("XY").box(
    base_length_x,
    base_width_y,
    base_height_z,
    centered=(True, True, False),
)

left_arm = cq.Workplane(
    "XY",
    origin=(-arm_center_x, 0.0, arm_bottom_z),
).box(
    arm_width_x,
    arm_depth_y,
    arm_height_z,
    centered=(True, True, False),
)

right_arm = cq.Workplane(
    "XY",
    origin=(arm_center_x, 0.0, arm_bottom_z),
).box(
    arm_width_x,
    arm_depth_y,
    arm_height_z,
    centered=(True, True, False),
)

left_hole = cq.Workplane(
    "XZ",
    origin=(-arm_center_x, hole_start_y, hole_center_z),
).circle(hole_radius).extrude(hole_length_y)

right_hole = cq.Workplane(
    "XZ",
    origin=(arm_center_x, hole_start_y, hole_center_z),
).circle(hole_radius).extrude(hole_length_y)

result = (
    base
    .union(left_arm)
    .union(right_arm)
    .cut(left_hole)
    .cut(right_hole)
    .clean()
)
