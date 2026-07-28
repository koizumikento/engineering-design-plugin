from build123d import Align, Box, Cylinder, Pos


outer_length = 100.0
outer_width = 70.0
outer_height = 30.0

side_wall_thickness = 4.0
bottom_thickness = 3.0
cavity_length = outer_length - 2.0 * side_wall_thickness
cavity_width = outer_width - 2.0 * side_wall_thickness
cavity_height = outer_height - bottom_thickness

boss_radius = 4.0
boss_height = 6.0
boss_z_min = bottom_thickness
boss_hole_radius = 1.5
boss_hole_height = boss_z_min + boss_height
boss_x_offset = 38.0
boss_y_offset = 23.0
boss_centers = (
    (-boss_x_offset, -boss_y_offset),
    (-boss_x_offset, boss_y_offset),
    (boss_x_offset, -boss_y_offset),
    (boss_x_offset, boss_y_offset),
)

outer = Box(
    outer_length,
    outer_width,
    outer_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
cavity = Pos(0.0, 0.0, bottom_thickness) * Box(
    cavity_length,
    cavity_width,
    cavity_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
enclosure = outer - cavity

for center_x, center_y in boss_centers:
    boss = Pos(center_x, center_y, boss_z_min) * Cylinder(
        boss_radius,
        boss_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    enclosure = enclosure + boss

for center_x, center_y in boss_centers:
    hole = Pos(center_x, center_y, 0.0) * Cylinder(
        boss_hole_radius,
        boss_hole_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    enclosure = enclosure - hole

result = enclosure.clean()
