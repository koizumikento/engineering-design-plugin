from math import cos, radians, sin

from build123d import Align, Cone, Cylinder, Pos


flange_radius = 40.0
flange_height = 12.0
outer_chamfer_size = 2.0

bore_radius = 15.0
bore_chamfer_size = 1.0

bolt_hole_radius = 4.0
pitch_circle_radius = 30.0
bolt_angles = (0.0, 60.0, 120.0, 180.0, 240.0, 300.0)

bottom_aligned = (Align.CENTER, Align.CENTER, Align.MIN)

outer_cylinder_height = flange_height - outer_chamfer_size
outer_body = Cylinder(
    flange_radius,
    outer_cylinder_height,
    align=bottom_aligned,
)
outer_chamfer = Pos(0.0, 0.0, outer_cylinder_height) * Cone(
    flange_radius,
    flange_radius - outer_chamfer_size,
    outer_chamfer_size,
    align=bottom_aligned,
)
flange = outer_body + outer_chamfer

bore_chamfer = Cone(
    bore_radius + bore_chamfer_size,
    bore_radius,
    bore_chamfer_size,
    align=bottom_aligned,
)
bore_cylinder = Pos(0.0, 0.0, bore_chamfer_size) * Cylinder(
    bore_radius,
    flange_height - bore_chamfer_size,
    align=bottom_aligned,
)
flange = flange - (bore_chamfer + bore_cylinder)

for angle in bolt_angles:
    x = pitch_circle_radius * cos(radians(angle))
    y = pitch_circle_radius * sin(radians(angle))
    bolt_hole = Pos(x, y, 0.0) * Cylinder(
        bolt_hole_radius,
        flange_height,
        align=bottom_aligned,
    )
    flange = flange - bolt_hole

result = flange.clean()
