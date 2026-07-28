import math

import cadquery as cq


# Nominal dimensions in millimetres.
flange_diameter = 80.0
flange_thickness = 12.0
outer_top_chamfer = 2.0

bore_diameter = 30.0
bore_bottom_chamfer = 1.0

bolt_hole_diameter = 8.0
pitch_circle_diameter = 60.0
bolt_angles_deg = (0.0, 60.0, 120.0, 180.0, 240.0, 300.0)

flange_radius = flange_diameter / 2.0
bore_radius = bore_diameter / 2.0
bolt_hole_radius = bolt_hole_diameter / 2.0
pitch_circle_radius = pitch_circle_diameter / 2.0

# R1 and R4: outer profile, including only the 2 x 2 mm top-edge chamfer.
outer_profile = (
    cq.Workplane("XZ")
    .moveTo(0.0, 0.0)
    .lineTo(flange_radius, 0.0)
    .lineTo(flange_radius, flange_thickness - outer_top_chamfer)
    .lineTo(flange_radius - outer_top_chamfer, flange_thickness)
    .lineTo(0.0, flange_thickness)
    .close()
)
flange = outer_profile.revolve(
    angleDegrees=360.0,
    axisStart=(0.0, 0.0),
    axisEnd=(0.0, 1.0),
)

# R2 and R5: concentric through-bore with only its 1 x 1 mm bottom chamfer.
bore_tool_extension = 1.0
bore_profile = (
    cq.Workplane("XZ")
    .moveTo(0.0, -bore_tool_extension)
    .lineTo(bore_radius + bore_bottom_chamfer, -bore_tool_extension)
    .lineTo(bore_radius + bore_bottom_chamfer, 0.0)
    .lineTo(bore_radius, bore_bottom_chamfer)
    .lineTo(bore_radius, flange_thickness + bore_tool_extension)
    .lineTo(0.0, flange_thickness + bore_tool_extension)
    .close()
)
bore_tool = bore_profile.revolve(
    angleDegrees=360.0,
    axisStart=(0.0, 0.0),
    axisEnd=(0.0, 1.0),
)

# R3: six equally spaced through-holes on the 60 mm pitch circle.
bolt_centres = [
    (
        pitch_circle_radius * math.cos(math.radians(angle)),
        pitch_circle_radius * math.sin(math.radians(angle)),
    )
    for angle in bolt_angles_deg
]
bolt_hole_tool = (
    cq.Workplane("XY", origin=(0.0, 0.0, -bore_tool_extension))
    .pushPoints(bolt_centres)
    .circle(bolt_hole_radius)
    .extrude(flange_thickness + 2.0 * bore_tool_extension)
)

# R6: no other edge treatments or features.
result = flange.cut(bore_tool).cut(bolt_hole_tool).clean()
