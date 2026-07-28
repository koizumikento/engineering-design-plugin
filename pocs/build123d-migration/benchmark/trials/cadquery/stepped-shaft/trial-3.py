import cadquery as cq


# Axial step dimensions (millimetres)
lower_diameter = 36.0
lower_z_min = 0.0
lower_z_max = 12.0

middle_diameter = 24.0
middle_z_min = 12.0
middle_z_max = 42.0

upper_diameter = 16.0
upper_z_min = 42.0
upper_z_max = 62.0

# Concentric through-bore
bore_diameter = 6.0
bore_z_min = 0.0
bore_z_max = 62.0

# Middle-step keyway cutter limits
keyway_x_min = -3.0
keyway_x_max = 3.0
keyway_y_min = 9.0
keyway_y_max = 20.0
keyway_z_min = 16.0
keyway_z_max = 38.0

# Upper outer top-edge chamfer
top_chamfer_size = 1.0


# R1-R3: coaxial stepped shaft, with the upper step chamfered before fusion.
lower_step = (
    cq.Workplane("XY", origin=(0.0, 0.0, lower_z_min))
    .circle(lower_diameter / 2.0)
    .extrude(lower_z_max - lower_z_min)
)
middle_step = (
    cq.Workplane("XY", origin=(0.0, 0.0, middle_z_min))
    .circle(middle_diameter / 2.0)
    .extrude(middle_z_max - middle_z_min)
)
upper_step = (
    cq.Workplane("XY", origin=(0.0, 0.0, upper_z_min))
    .circle(upper_diameter / 2.0)
    .extrude(upper_z_max - upper_z_min)
    .edges(">Z")
    .chamfer(top_chamfer_size)
)

# R4: fuse the steps and prepare the full-height concentric bore.
shaft = lower_step.union(middle_step).union(upper_step)
bore = (
    cq.Workplane("XY", origin=(0.0, 0.0, bore_z_min))
    .circle(bore_diameter / 2.0)
    .extrude(bore_z_max - bore_z_min)
)

# R5: cutter spans the specified Cartesian limits and opens toward +Y.
keyway = (
    cq.Workplane(
        "XY",
        origin=(
            (keyway_x_min + keyway_x_max) / 2.0,
            (keyway_y_min + keyway_y_max) / 2.0,
            keyway_z_min,
        ),
    )
    .box(
        keyway_x_max - keyway_x_min,
        keyway_y_max - keyway_y_min,
        keyway_z_max - keyway_z_min,
        centered=(True, True, False),
    )
)

# R4-R7: one hollow, keyed solid with no additional edge treatments.
result = shaft.cut(bore).cut(keyway).clean()
