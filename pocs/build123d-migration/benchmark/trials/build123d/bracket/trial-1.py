from build123d import Align, Box, Cylinder, Plane, Polygon, Pos, Rot, extrude


foot_width = 60.0
foot_depth = 40.0
foot_thickness = 8.0

plate_width = 60.0
plate_thickness = 8.0
plate_height = 40.0
plate_y_min = 12.0

foot_hole_radius = 3.0
foot_hole_centres = ((-20.0, -5.0), (20.0, -5.0))

plate_hole_radius = 4.0
plate_hole_centres = ((-18.0, 28.0), (18.0, 28.0))

inside_fillet_radius = 4.0
inside_fillet_y_min = 8.0
inside_fillet_z_min = 8.0
inside_fillet_axis_y = 8.0
inside_fillet_axis_z = 12.0

rib_width = 6.0
rib_yz_vertices = ((0.0, 8.0), (12.0, 8.0), (12.0, 20.0))


foot = Box(
    foot_width,
    foot_depth,
    foot_thickness,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

plate = Pos(0.0, plate_y_min, foot_thickness) * Box(
    plate_width,
    plate_thickness,
    plate_height,
    align=(Align.CENTER, Align.MIN, Align.MIN),
)

fillet_envelope = Pos(
    0.0,
    inside_fillet_y_min,
    inside_fillet_z_min,
) * Box(
    foot_width,
    inside_fillet_radius,
    inside_fillet_radius,
    align=(Align.CENTER, Align.MIN, Align.MIN),
)

fillet_cylinder = (
    Pos(
        -foot_width / 2.0,
        inside_fillet_axis_y,
        inside_fillet_axis_z,
    )
    * Rot(0.0, 90.0, 0.0)
    * Cylinder(
        inside_fillet_radius,
        foot_width,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
)
inside_fillet = fillet_envelope - fillet_cylinder

rib_profile = Plane.YZ * Polygon(*rib_yz_vertices)
rib = extrude(rib_profile, amount=rib_width / 2.0, both=True)

part = foot + plate + inside_fillet + rib

for hole_x, hole_y in foot_hole_centres:
    foot_hole = Pos(hole_x, hole_y, 0.0) * Cylinder(
        foot_hole_radius,
        foot_thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    part = part - foot_hole

for hole_x, hole_z in plate_hole_centres:
    plate_hole = (
        Pos(hole_x, plate_y_min, hole_z)
        * Rot(-90.0, 0.0, 0.0)
        * Cylinder(
            plate_hole_radius,
            plate_thickness,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )
    part = part - plate_hole

result = part.clean()
