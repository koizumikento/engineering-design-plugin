from build123d import Align, Axis, Box, Cylinder, Pos, fillet


block_x = 50.0
block_y = 40.0
block_z = 20.0
vertical_edge_radius = 3.0

hole_diameter = 5.0
hole_radius = hole_diameter / 2.0
hole_x_offsets = (-15.0, 15.0)
hole_y_offsets = (-10.0, 10.0)

pocket_x = 20.0
pocket_y = 12.0
pocket_depth = 4.0
pocket_bottom_z = block_z - pocket_depth

base = Box(
    block_x,
    block_y,
    block_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
rounded_base = fillet(
    base.edges().filter_by(Axis.Z),
    radius=vertical_edge_radius,
)

holes = [
    Pos(x, y, 0.0)
    * Cylinder(
        hole_radius,
        block_z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    for x in hole_x_offsets
    for y in hole_y_offsets
]

pocket = Pos(0.0, 0.0, pocket_bottom_z) * Box(
    pocket_x,
    pocket_y,
    pocket_depth,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

result = (rounded_base - holes[0] - holes[1] - holes[2] - holes[3] - pocket).clean()
