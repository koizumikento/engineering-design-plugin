import cadquery as cq


lower_diameter = 36.0
lower_z_min = 0.0
lower_z_max = 12.0

middle_diameter = 24.0
middle_z_min = 12.0
middle_z_max = 42.0

upper_diameter = 16.0
upper_z_min = 42.0
upper_cylinder_z_max = 61.0
upper_z_max = 62.0

bore_diameter = 6.0

keyway_x_min = -3.0
keyway_x_max = 3.0
keyway_y_min = 9.0
keyway_y_max = 20.0
keyway_z_min = 16.0
keyway_z_max = 38.0

chamfer_radial_size = 1.0
chamfer_axial_size = 1.0

lower_radius = lower_diameter / 2.0
middle_radius = middle_diameter / 2.0
upper_radius = upper_diameter / 2.0
bore_radius = bore_diameter / 2.0
upper_top_radius = upper_radius - chamfer_radial_size

lower_step = (
    cq.Workplane("XY", origin=(0.0, 0.0, lower_z_min))
    .circle(lower_radius)
    .extrude(lower_z_max - lower_z_min)
)

middle_step = (
    cq.Workplane("XY", origin=(0.0, 0.0, middle_z_min))
    .circle(middle_radius)
    .extrude(middle_z_max - middle_z_min)
)

upper_step = (
    cq.Workplane("XY", origin=(0.0, 0.0, upper_z_min))
    .circle(upper_radius)
    .extrude(upper_cylinder_z_max - upper_z_min)
)

upper_chamfer = (
    cq.Workplane("XY", origin=(0.0, 0.0, upper_cylinder_z_max))
    .circle(upper_radius)
    .workplane(offset=chamfer_axial_size)
    .circle(upper_top_radius)
    .loft(combine=True)
)

shaft = (
    lower_step
    .union(middle_step)
    .union(upper_step)
    .union(upper_chamfer)
    .clean()
)

bore = (
    cq.Workplane("XY", origin=(0.0, 0.0, lower_z_min))
    .circle(bore_radius)
    .extrude(upper_z_max - lower_z_min)
)

keyway = (
    cq.Workplane(
        "XY",
        origin=(keyway_x_min, keyway_y_min, keyway_z_min),
    )
    .box(
        keyway_x_max - keyway_x_min,
        keyway_y_max - keyway_y_min,
        keyway_z_max - keyway_z_min,
        centered=(False, False, False),
    )
)

result = shaft.cut(bore).cut(keyway).clean()
