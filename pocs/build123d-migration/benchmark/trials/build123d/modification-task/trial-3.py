from build123d import Align, Box, Cylinder, Pos


plate_length = 70
plate_width = 40
plate_thickness = 8

preserved_hole_radius = 3
preserved_hole_centers = (
    (-25, -12),
    (-25, 12),
    (25, -12),
)

pocket_length = 16
pocket_width = 6
pocket_depth = 2
pocket_center_x = 0
pocket_center_y = -12
pocket_bottom_z = 6

new_hole_radius = 5
new_hole_center_x = 15
new_hole_center_y = 8

boss_radius = 8
boss_height = 5
boss_bottom_z = 8

boss_bore_radius = 3
boss_bore_height = 13

plate = Box(
    plate_length,
    plate_width,
    plate_thickness,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

boss = Pos(0, 0, boss_bottom_z) * Cylinder(
    boss_radius,
    boss_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

revised_part = plate + boss

pocket = Pos(pocket_center_x, pocket_center_y, pocket_bottom_z) * Box(
    pocket_length,
    pocket_width,
    pocket_depth,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
revised_part = revised_part - pocket

for hole_x, hole_y in preserved_hole_centers:
    preserved_hole = Pos(hole_x, hole_y, 0) * Cylinder(
        preserved_hole_radius,
        plate_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    revised_part = revised_part - preserved_hole

new_hole = Pos(new_hole_center_x, new_hole_center_y, 0) * Cylinder(
    new_hole_radius,
    plate_thickness,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
revised_part = revised_part - new_hole

boss_bore = Cylinder(
    boss_bore_radius,
    boss_bore_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

result = (revised_part - boss_bore).clean()
