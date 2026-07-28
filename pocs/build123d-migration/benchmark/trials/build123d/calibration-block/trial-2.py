from build123d import Align, Axis, Box, Cylinder, Pos, fillet


block_x = 50.0
block_y = 40.0
block_z = 20.0
vertical_edge_radius = 3.0

hole_diameter = 5.0
hole_radius = hole_diameter / 2.0
hole_centers = (
    (-15.0, -10.0),
    (-15.0, 10.0),
    (15.0, -10.0),
    (15.0, 10.0),
)

pocket_x = 20.0
pocket_y = 12.0
pocket_depth = 4.0
pocket_bottom_z = block_z - pocket_depth

block = Box(
    block_x,
    block_y,
    block_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
vertical_edges = block.edges().filter_by(Axis.Z)
part = fillet(vertical_edges, radius=vertical_edge_radius)

for hole_x, hole_y in hole_centers:
    hole = Pos(hole_x, hole_y, 0.0) * Cylinder(
        hole_radius,
        block_z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    part = part - hole

pocket = Pos(0.0, 0.0, pocket_bottom_z) * Box(
    pocket_x,
    pocket_y,
    pocket_depth,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

result = (part - pocket).clean()
