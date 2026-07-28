from math import cos, radians, sin

from build123d import Align, Cone, Cylinder, Pos


flange_radius = 40.0
flange_thickness = 12.0
outer_chamfer_size = 2.0

bore_radius = 15.0
bore_bottom_chamfer_size = 1.0

bolt_hole_radius = 4.0
pitch_circle_radius = 30.0
bolt_angles = (0.0, 60.0, 120.0, 180.0, 240.0, 300.0)

bottom_cylinder_height = flange_thickness - outer_chamfer_size
outer_body = Cylinder(
    flange_radius,
    bottom_cylinder_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
outer_top_chamfer = Pos(0, 0, bottom_cylinder_height) * Cone(
    flange_radius,
    flange_radius - outer_chamfer_size,
    outer_chamfer_size,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
flange_blank = outer_body + outer_top_chamfer

bore_chamfer = Cone(
    bore_radius + bore_bottom_chamfer_size,
    bore_radius,
    bore_bottom_chamfer_size,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
bore_cylinder = Pos(0, 0, bore_bottom_chamfer_size) * Cylinder(
    bore_radius,
    flange_thickness - bore_bottom_chamfer_size,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
bore_tool = bore_chamfer + bore_cylinder

bolt_hole_tools = [
    Pos(
        pitch_circle_radius * cos(radians(angle)),
        pitch_circle_radius * sin(radians(angle)),
        0,
    )
    * Cylinder(
        bolt_hole_radius,
        flange_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    for angle in bolt_angles
]

result = (flange_blank - bore_tool - bolt_hole_tools).clean()
