import cadquery as cq


# R1: foot
foot_width_x = 60.0
foot_depth_y = 40.0
foot_thickness_z = 8.0

# R2: vertical plate
plate_width_x = 60.0
plate_thickness_y = 8.0
plate_height_z = 40.0
plate_y_min = 12.0

# R3: foot holes
foot_hole_diameter = 6.0
foot_hole_centres = [(-20.0, -5.0), (20.0, -5.0)]

# R4: vertical-plate holes
plate_hole_diameter = 8.0
plate_hole_centres_xz = [(-18.0, 28.0), (18.0, 28.0)]

# R5: inside corner fillet
inside_fillet_radius = 4.0
fillet_y_min = 8.0
fillet_z_min = 8.0

# R6: centred triangular rib
rib_width_x = 6.0
rib_vertices_yz = [(0.0, 8.0), (12.0, 8.0), (12.0, 20.0)]


foot = (
    cq.Workplane("XY")
    .box(
        foot_width_x,
        foot_depth_y,
        foot_thickness_z,
        centered=(True, True, False),
    )
)

plate_y_center = plate_y_min + plate_thickness_y / 2.0
plate = (
    cq.Workplane("XY", origin=(0.0, plate_y_center, foot_thickness_z))
    .box(
        plate_width_x,
        plate_thickness_y,
        plate_height_z,
        centered=(True, True, False),
    )
)

# The concave fillet occupies the 4 x 4 corner square outside a radius-4
# cylinder whose axis is X, leaving tangencies at Y=8 and Z=12.
fillet_square = (
    cq.Workplane(
        "XY",
        origin=(
            0.0,
            fillet_y_min + inside_fillet_radius / 2.0,
            fillet_z_min,
        ),
    )
    .box(
        foot_width_x,
        inside_fillet_radius,
        inside_fillet_radius,
        centered=(True, True, False),
    )
)
fillet_cylinder = (
    cq.Workplane(
        "YZ",
        origin=(
            -foot_width_x / 2.0,
            fillet_y_min,
            fillet_z_min + inside_fillet_radius,
        ),
    )
    .circle(inside_fillet_radius)
    .extrude(foot_width_x)
)
inside_fillet = fillet_square.cut(fillet_cylinder)

rib = (
    cq.Workplane("YZ", origin=(-rib_width_x / 2.0, 0.0, 0.0))
    .moveTo(*rib_vertices_yz[0])
    .lineTo(*rib_vertices_yz[1])
    .lineTo(*rib_vertices_yz[2])
    .close()
    .extrude(rib_width_x)
)

foot_holes = (
    cq.Workplane("XY")
    .pushPoints(foot_hole_centres)
    .circle(foot_hole_diameter / 2.0)
    .extrude(foot_thickness_z)
)

# CadQuery's XZ plane has its positive normal along -Y, so starting at the
# plate rear face and extruding positively spans Y=20 down to Y=12.
plate_y_max = plate_y_min + plate_thickness_y
plate_holes = (
    cq.Workplane("XZ", origin=(0.0, plate_y_max, 0.0))
    .pushPoints(plate_hole_centres_xz)
    .circle(plate_hole_diameter / 2.0)
    .extrude(plate_thickness_y)
)

result = (
    foot.union(plate)
    .union(inside_fillet)
    .union(rib)
    .cut(foot_holes)
    .cut(plate_holes)
    .clean()
)
