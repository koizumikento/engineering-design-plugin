from math import cos, radians, sin

from build123d import Align, Cone, Cylinder, Pos


flange_radius = 40.0
flange_thickness = 12.0
outer_chamfer_size = 2.0

bore_radius = 15.0
bore_bottom_chamfer_size = 1.0

bolt_hole_radius = 4.0
bolt_pitch_radius = 30.0
bolt_angles = (0.0, 60.0, 120.0, 180.0, 240.0, 300.0)

z_min_align = (Align.CENTER, Align.CENTER, Align.MIN)

straight_outer_height = flange_thickness - outer_chamfer_size
body = Cylinder(flange_radius, straight_outer_height, align=z_min_align)
outer_chamfer = Pos(0, 0, straight_outer_height) * Cone(
    flange_radius,
    flange_radius - outer_chamfer_size,
    outer_chamfer_size,
    align=z_min_align,
)
body = body + outer_chamfer

bore_bottom_chamfer = Cone(
    bore_radius + bore_bottom_chamfer_size,
    bore_radius,
    bore_bottom_chamfer_size,
    align=z_min_align,
)
bore_straight = Pos(0, 0, bore_bottom_chamfer_size) * Cylinder(
    bore_radius,
    flange_thickness - bore_bottom_chamfer_size,
    align=z_min_align,
)
bore_tool = bore_bottom_chamfer + bore_straight

bolt_holes = None
for angle in bolt_angles:
    angle_radians = radians(angle)
    center_x = bolt_pitch_radius * cos(angle_radians)
    center_y = bolt_pitch_radius * sin(angle_radians)
    hole = Pos(center_x, center_y, 0) * Cylinder(
        bolt_hole_radius,
        flange_thickness,
        align=z_min_align,
    )
    bolt_holes = hole if bolt_holes is None else bolt_holes + hole

result = (body - bore_tool - bolt_holes).clean()
