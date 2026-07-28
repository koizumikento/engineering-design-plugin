import math

import cadquery as cq


flange_radius = 40.0
flange_thickness = 12.0
bore_radius = 15.0
bolt_hole_radius = 4.0
pitch_circle_radius = 30.0
bolt_count = 6
outer_top_chamfer = 2.0
bore_bottom_chamfer = 1.0

flange = (
    cq.Workplane("XY", origin=(0.0, 0.0, 0.0))
    .circle(flange_radius)
    .extrude(flange_thickness)
    .faces(">Z")
    .edges()
    .chamfer(outer_top_chamfer)
)

bolt_positions = [
    (
        pitch_circle_radius * math.cos(math.radians(index * 360.0 / bolt_count)),
        pitch_circle_radius * math.sin(math.radians(index * 360.0 / bolt_count)),
    )
    for index in range(bolt_count)
]
bolt_holes = (
    cq.Workplane("XY", origin=(0.0, 0.0, 0.0))
    .pushPoints(bolt_positions)
    .circle(bolt_hole_radius)
    .extrude(flange_thickness)
)

bore_cylinder = (
    cq.Workplane("XY", origin=(0.0, 0.0, bore_bottom_chamfer))
    .circle(bore_radius)
    .extrude(flange_thickness - bore_bottom_chamfer)
)
bore_chamfer = (
    cq.Workplane("XY", origin=(0.0, 0.0, 0.0))
    .circle(bore_radius + bore_bottom_chamfer)
    .workplane(offset=bore_bottom_chamfer)
    .circle(bore_radius)
    .loft(combine=True)
)

result = flange.cut(bolt_holes).cut(bore_cylinder).cut(bore_chamfer).clean()
