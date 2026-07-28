import math

import cadquery as cq


outer_diameter = 80.0
flange_thickness = 12.0
central_bore_diameter = 30.0
bolt_hole_diameter = 8.0
pitch_circle_diameter = 60.0
bolt_count = 6
outer_top_chamfer = 2.0
central_bore_bottom_chamfer = 1.0

outer_radius = outer_diameter / 2.0
central_bore_radius = central_bore_diameter / 2.0
bolt_hole_radius = bolt_hole_diameter / 2.0
pitch_circle_radius = pitch_circle_diameter / 2.0

radial_profile = [
    (central_bore_radius + central_bore_bottom_chamfer, 0.0),
    (outer_radius, 0.0),
    (outer_radius, flange_thickness - outer_top_chamfer),
    (outer_radius - outer_top_chamfer, flange_thickness),
    (central_bore_radius, flange_thickness),
    (central_bore_radius, central_bore_bottom_chamfer),
]

flange = (
    cq.Workplane("XZ")
    .polyline(radial_profile)
    .close()
    .revolve(360.0, (0.0, 0.0), (0.0, 1.0))
)

bolt_positions = [
    (
        pitch_circle_radius * math.cos(math.radians(index * 360.0 / bolt_count)),
        pitch_circle_radius * math.sin(math.radians(index * 360.0 / bolt_count)),
    )
    for index in range(bolt_count)
]

bolt_holes = (
    cq.Workplane("XY")
    .pushPoints(bolt_positions)
    .circle(bolt_hole_radius)
    .extrude(flange_thickness)
)

result = flange.cut(bolt_holes).clean()
