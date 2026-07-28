from build123d import Align, Box, Cylinder, Plane, Polygon, Pos, Rot, extrude, fillet


# Primary envelope dimensions
foot_x = 60.0
foot_y = 40.0
foot_z = 8.0
plate_x = 60.0
plate_y = 8.0
plate_z = 40.0

# Primary feature locations
plate_y_min = 12.0
plate_z_min = 8.0
inside_corner_y = 12.0
inside_corner_z = 8.0
inside_fillet_radius = 4.0

# Hole dimensions and locations
foot_hole_radius = 3.0
foot_hole_centers = ((-20.0, -5.0), (20.0, -5.0))
plate_hole_radius = 4.0
plate_hole_centers = ((-18.0, 28.0), (18.0, 28.0))

# Rib dimensions and YZ profile
rib_x_min = -3.0
rib_x_width = 6.0
rib_yz_vertices = ((0.0, 8.0), (12.0, 8.0), (12.0, 20.0))

foot = Box(
    foot_x,
    foot_y,
    foot_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

plate = Pos(0.0, plate_y_min, plate_z_min) * Box(
    plate_x,
    plate_y,
    plate_z,
    align=(Align.CENTER, Align.MIN, Align.MIN),
)

body = (foot + plate).clean()

inside_corner_edge = next(
    edge
    for edge in body.edges()
    if abs(edge.center().Y - inside_corner_y) < 1.0e-7
    and abs(edge.center().Z - inside_corner_z) < 1.0e-7
)
body = fillet([inside_corner_edge], radius=inside_fillet_radius).clean()

rib_profile = Plane.YZ * Polygon(*rib_yz_vertices)
rib = Pos(rib_x_min, 0.0, 0.0) * extrude(rib_profile, amount=rib_x_width)
body = (body + rib).clean()

for hole_x, hole_y in foot_hole_centers:
    foot_hole = Pos(hole_x, hole_y, 0.0) * Cylinder(
        foot_hole_radius,
        foot_z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = body - foot_hole

for hole_x, hole_z in plate_hole_centers:
    plate_hole = (
        Pos(hole_x, plate_y_min, hole_z)
        * Rot(-90.0, 0.0, 0.0)
        * Cylinder(
            plate_hole_radius,
            plate_y,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )
    body = body - plate_hole

result = body.clean()
