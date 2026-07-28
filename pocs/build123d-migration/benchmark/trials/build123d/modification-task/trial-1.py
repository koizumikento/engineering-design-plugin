from build123d import Align, Box, Cylinder, Pos


plate_length = 70.0
plate_width = 40.0
plate_thickness = 8.0

preserved_hole_radius = 3.0
preserved_hole_centres = (
    (-25.0, -12.0),
    (-25.0, 12.0),
    (25.0, -12.0),
)

pocket_length = 16.0
pocket_width = 6.0
pocket_depth = 2.0
pocket_centre_y = -12.0
pocket_bottom_z = plate_thickness - pocket_depth

relocated_hole_radius = 5.0
relocated_hole_centre = (15.0, 8.0)

boss_radius = 8.0
boss_height = 5.0
boss_bottom_z = plate_thickness

boss_bore_radius = 3.0
boss_bore_height = plate_thickness + boss_height

plate = Box(
    plate_length,
    plate_width,
    plate_thickness,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

boss = Pos(0.0, 0.0, boss_bottom_z) * Cylinder(
    boss_radius,
    boss_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

preserved_holes = [
    Pos(x, y, 0.0)
    * Cylinder(
        preserved_hole_radius,
        plate_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    for x, y in preserved_hole_centres
]

relocated_hole = Pos(*relocated_hole_centre, 0.0) * Cylinder(
    relocated_hole_radius,
    plate_thickness,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

pocket = Pos(0.0, pocket_centre_y, pocket_bottom_z) * Box(
    pocket_length,
    pocket_width,
    pocket_depth,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

boss_bore = Cylinder(
    boss_bore_radius,
    boss_bore_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

result = (plate + boss).clean()
for hole in preserved_holes:
    result = result - hole
result = (result - relocated_hole - pocket - boss_bore).clean()
