import cadquery as cq


base_width = 50.0
base_depth = 30.0
base_height = 10.0

arm_width = 10.0
arm_depth = 30.0
arm_height = 40.0
arm_center_offset = 20.0

hole_diameter = 8.0
hole_center_height = 38.0

base = cq.Workplane("XY").box(
    base_width,
    base_depth,
    base_height,
    centered=(True, True, False),
)

left_arm = cq.Workplane(
    "XY",
    origin=(-arm_center_offset, 0.0, base_height),
).box(
    arm_width,
    arm_depth,
    arm_height,
    centered=(True, True, False),
)

right_arm = cq.Workplane(
    "XY",
    origin=(arm_center_offset, 0.0, base_height),
).box(
    arm_width,
    arm_depth,
    arm_height,
    centered=(True, True, False),
)

left_hole = cq.Workplane(
    "XZ",
    origin=(-arm_center_offset, arm_depth / 2.0, hole_center_height),
).circle(hole_diameter / 2.0).extrude(arm_depth)

right_hole = cq.Workplane(
    "XZ",
    origin=(arm_center_offset, arm_depth / 2.0, hole_center_height),
).circle(hole_diameter / 2.0).extrude(arm_depth)

result = (
    base
    .union(left_arm)
    .union(right_arm)
    .cut(left_hole)
    .cut(right_hole)
    .clean()
)
