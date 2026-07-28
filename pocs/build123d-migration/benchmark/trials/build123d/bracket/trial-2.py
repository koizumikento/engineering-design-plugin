from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Cylinder,
    Plane,
    Polygon,
    Pos,
    Rot,
    extrude,
)


# Nominal dimensions (mm)
foot_x = 60
foot_y = 40
foot_z = 8

plate_x = 60
plate_y = 8
plate_z = 40
plate_y_min = 12
plate_z_min = 8

foot_hole_radius = 3
foot_hole_x = 20
foot_hole_y = -5

plate_hole_radius = 4
plate_hole_x = 18
plate_hole_z = 28

corner_radius = 4
corner_y_tangent = 8
corner_y = 12
corner_z = 8
corner_z_tangent = 12

rib_x_min = -3
rib_x_max = 3
rib_vertices_yz = ((0, 8), (12, 8), (12, 20))


foot = Box(
    foot_x,
    foot_y,
    foot_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

plate = Pos(0, plate_y_min + plate_y / 2, plate_z_min) * Box(
    plate_x,
    plate_y,
    plate_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

# The concave internal fillet is the part of the 4x4 corner prism outside
# the tangent radius-4 cylinder.
corner_prism = Pos(
    0,
    (corner_y_tangent + corner_y) / 2,
    corner_z,
) * Box(
    foot_x,
    corner_y - corner_y_tangent,
    corner_z_tangent - corner_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
corner_cylinder = (
    Pos(-foot_x / 2, corner_y_tangent, corner_z_tangent)
    * Rot(0, 90, 0)
    * Cylinder(
        corner_radius,
        foot_x,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
)
corner_fillet = corner_prism - corner_cylinder

with BuildPart() as rib_builder:
    with BuildSketch(Plane.YZ.offset(rib_x_min)):
        Polygon(*rib_vertices_yz)
    extrude(amount=rib_x_max - rib_x_min)
rib = rib_builder.part

foot_holes = [
    Pos(x, foot_hole_y, 0)
    * Cylinder(
        foot_hole_radius,
        foot_z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    for x in (-foot_hole_x, foot_hole_x)
]

plate_holes = [
    Pos(x, plate_y_min, plate_hole_z)
    * Rot(-90, 0, 0)
    * Cylinder(
        plate_hole_radius,
        plate_y,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    for x in (-plate_hole_x, plate_hole_x)
]

result = (
    foot
    + plate
    + corner_fillet
    + rib
    - foot_holes[0]
    - foot_holes[1]
    - plate_holes[0]
    - plate_holes[1]
).clean()
