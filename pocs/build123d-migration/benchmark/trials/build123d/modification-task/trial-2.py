from build123d import Align, Box, Cylinder, Pos


plate_length_x = 70.0
plate_width_y = 40.0
plate_height_z = 8.0
plate_z_min = 0.0

preserved_hole_diameter = 6.0
preserved_hole_radius = preserved_hole_diameter / 2.0
preserved_hole_centres = (
    (-25.0, -12.0),
    (-25.0, 12.0),
    (25.0, -12.0),
)

pocket_length_x = 16.0
pocket_width_y = 6.0
pocket_depth_z = 2.0
pocket_centre_x = 0.0
pocket_centre_y = -12.0
pocket_z_min = plate_height_z - pocket_depth_z

new_hole_diameter = 10.0
new_hole_radius = new_hole_diameter / 2.0
new_hole_centre_x = 15.0
new_hole_centre_y = 8.0

boss_diameter = 16.0
boss_radius = boss_diameter / 2.0
boss_height_z = 5.0
boss_centre_x = 0.0
boss_centre_y = 0.0
boss_z_min = plate_height_z

bore_diameter = 6.0
bore_radius = bore_diameter / 2.0
bore_centre_x = 0.0
bore_centre_y = 0.0
bore_height_z = plate_height_z + boss_height_z

plate = Box(
    plate_length_x,
    plate_width_y,
    plate_height_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

boss = Pos(boss_centre_x, boss_centre_y, boss_z_min) * Cylinder(
    boss_radius,
    boss_height_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

part = plate + boss

pocket = Pos(pocket_centre_x, pocket_centre_y, pocket_z_min) * Box(
    pocket_length_x,
    pocket_width_y,
    pocket_depth_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
part = part - pocket

for hole_centre_x, hole_centre_y in preserved_hole_centres:
    preserved_hole = Pos(hole_centre_x, hole_centre_y, plate_z_min) * Cylinder(
        preserved_hole_radius,
        plate_height_z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    part = part - preserved_hole

new_hole = Pos(new_hole_centre_x, new_hole_centre_y, plate_z_min) * Cylinder(
    new_hole_radius,
    plate_height_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
part = part - new_hole

bore = Pos(bore_centre_x, bore_centre_y, plate_z_min) * Cylinder(
    bore_radius,
    bore_height_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

result = (part - bore).clean()
