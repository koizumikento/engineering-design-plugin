from build123d import Align, Box, Cylinder, Pos


block_x = 50.0
block_y = 40.0
block_z = 20.0
corner_radius = 3.0

hole_radius = 2.5
hole_x = 15.0
hole_y = 10.0

pocket_x = 20.0
pocket_y = 12.0
pocket_depth = 4.0

xy_centered_z_min = (Align.CENTER, Align.CENTER, Align.MIN)

straight_x = block_x - 2.0 * corner_radius
straight_y = block_y - 2.0 * corner_radius
corner_x = block_x / 2.0 - corner_radius
corner_y = block_y / 2.0 - corner_radius

body = (
    Box(straight_x, block_y, block_z, align=xy_centered_z_min)
    + Box(block_x, straight_y, block_z, align=xy_centered_z_min)
)

for x in (-corner_x, corner_x):
    for y in (-corner_y, corner_y):
        body = body + Pos(x, y, 0.0) * Cylinder(
            corner_radius,
            block_z,
            align=xy_centered_z_min,
        )

for x in (-hole_x, hole_x):
    for y in (-hole_y, hole_y):
        body = body - Pos(x, y, 0.0) * Cylinder(
            hole_radius,
            block_z,
            align=xy_centered_z_min,
        )

pocket = Pos(0.0, 0.0, block_z - pocket_depth) * Box(
    pocket_x,
    pocket_y,
    pocket_depth,
    align=xy_centered_z_min,
)

result = (body - pocket).clean()
