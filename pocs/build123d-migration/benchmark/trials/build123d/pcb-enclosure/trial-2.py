from build123d import Align, Box, Cylinder, Pos


outer_x = 100.0
outer_y = 70.0
outer_z = 30.0

cavity_x = 92.0
cavity_y = 62.0
cavity_z_min = 3.0
cavity_z_max = 30.0
cavity_height = cavity_z_max - cavity_z_min

boss_radius = 4.0
boss_z_min = 3.0
boss_z_max = 9.0
boss_height = boss_z_max - boss_z_min
boss_x_positions = (-38.0, 38.0)
boss_y_positions = (-23.0, 23.0)

hole_radius = 1.5
hole_z_min = 0.0
hole_z_max = 9.0
hole_height = hole_z_max - hole_z_min

centered_on_xy_and_min_z = (Align.CENTER, Align.CENTER, Align.MIN)

outer = Box(
    outer_x,
    outer_y,
    outer_z,
    align=centered_on_xy_and_min_z,
)
cavity = Pos(0, 0, cavity_z_min) * Box(
    cavity_x,
    cavity_y,
    cavity_height,
    align=centered_on_xy_and_min_z,
)

result = outer - cavity

for boss_x in boss_x_positions:
    for boss_y in boss_y_positions:
        boss = Pos(boss_x, boss_y, boss_z_min) * Cylinder(
            boss_radius,
            boss_height,
            align=centered_on_xy_and_min_z,
        )
        result = result + boss

for hole_x in boss_x_positions:
    for hole_y in boss_y_positions:
        hole = Pos(hole_x, hole_y, hole_z_min) * Cylinder(
            hole_radius,
            hole_height,
            align=centered_on_xy_and_min_z,
        )
        result = result - hole

result = result.clean()
