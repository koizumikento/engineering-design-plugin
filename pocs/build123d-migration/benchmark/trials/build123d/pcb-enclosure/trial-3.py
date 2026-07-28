from build123d import Align, Box, Cylinder, Pos


outer_x = 100.0
outer_y = 70.0
outer_z = 30.0

wall_thickness = 4.0
bottom_thickness = 3.0
cavity_x = outer_x - 2.0 * wall_thickness
cavity_y = outer_y - 2.0 * wall_thickness
cavity_z = outer_z - bottom_thickness

boss_radius = 4.0
boss_base_z = bottom_thickness
boss_top_z = 9.0
boss_height = boss_top_z - boss_base_z
boss_x = 38.0
boss_y = 23.0

hole_radius = 1.5
hole_base_z = 0.0
hole_top_z = boss_top_z
hole_height = hole_top_z - hole_base_z

center_min = (Align.CENTER, Align.CENTER, Align.MIN)

outer = Box(outer_x, outer_y, outer_z, align=center_min)
cavity = Pos(0.0, 0.0, bottom_thickness) * Box(
    cavity_x,
    cavity_y,
    cavity_z,
    align=center_min,
)
enclosure = outer - cavity

boss_centers = (
    (-boss_x, -boss_y),
    (-boss_x, boss_y),
    (boss_x, -boss_y),
    (boss_x, boss_y),
)

for center_x, center_y in boss_centers:
    boss = Pos(center_x, center_y, boss_base_z) * Cylinder(
        boss_radius,
        boss_height,
        align=center_min,
    )
    enclosure = enclosure + boss

for center_x, center_y in boss_centers:
    hole = Pos(center_x, center_y, hole_base_z) * Cylinder(
        hole_radius,
        hole_height,
        align=center_min,
    )
    enclosure = enclosure - hole

result = enclosure.clean()
