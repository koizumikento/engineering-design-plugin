import cadquery as cq


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
hole_start_y = 15.0
hole_length = 30.0

base = cq.Workplane("XY").box(
    base_width,
    base_depth,
    base_height,
    centered=(True, True, False),
)

left_arm = cq.Workplane(
    "XY",
    origin=(-arm_center_x, 0.0, arm_bottom_z),
).box(
    arm_width,
    arm_depth,
    arm_height,
    centered=(True, True, False),
)

right_arm = cq.Workplane(
    "XY",
    origin=(arm_center_x, 0.0, arm_bottom_z),
).box(
    arm_width,
    arm_depth,
    arm_height,
    centered=(True, True, False),
)

through_holes = (
    cq.Workplane("XZ", origin=(0.0, hole_start_y, 0.0))
    .pushPoints(
        [
            (-arm_center_x, hole_center_z),
            (arm_center_x, hole_center_z),
        ]
    )
    .circle(hole_radius)
    .extrude(hole_length)
)

result = base.union(left_arm).union(right_arm).cut(through_holes).clean()
