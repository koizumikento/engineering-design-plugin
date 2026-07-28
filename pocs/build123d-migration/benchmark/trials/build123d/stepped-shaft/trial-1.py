from build123d import Align, Box, Cylinder, Pos, chamfer


lower_radius = 18.0
lower_height = 12.0

middle_radius = 12.0
middle_z_min = 12.0
middle_height = 30.0

upper_radius = 8.0
upper_z_min = 42.0
upper_height = 20.0

bore_radius = 3.0
overall_height = 62.0

keyway_width = 6.0
keyway_y_min = 9.0
keyway_y_max = 20.0
keyway_z_min = 16.0
keyway_z_max = 38.0

top_chamfer_size = 1.0

lower_step = Cylinder(
    lower_radius,
    lower_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
middle_step = Pos(0, 0, middle_z_min) * Cylinder(
    middle_radius,
    middle_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
upper_step = Pos(0, 0, upper_z_min) * Cylinder(
    upper_radius,
    upper_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

shaft = (lower_step + middle_step + upper_step).clean()

bore = Cylinder(
    bore_radius,
    overall_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
keyway = Pos(0, keyway_y_min, keyway_z_min) * Box(
    keyway_width,
    keyway_y_max - keyway_y_min,
    keyway_z_max - keyway_z_min,
    align=(Align.CENTER, Align.MIN, Align.MIN),
)

shaft = (shaft - bore - keyway).clean()

top_planar_edges = [
    edge
    for edge in shaft.edges()
    if abs(edge.bounding_box().min.Z - overall_height) < 1.0e-7
    and abs(edge.bounding_box().max.Z - overall_height) < 1.0e-7
]
upper_outer_top_edge = max(top_planar_edges, key=lambda edge: edge.length)

result = chamfer([upper_outer_top_edge], length=top_chamfer_size).clean()
