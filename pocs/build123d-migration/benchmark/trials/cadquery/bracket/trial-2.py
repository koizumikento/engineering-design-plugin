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
plate_z_min = 8.0

# R3: foot holes
foot_hole_diameter = 6.0
foot_hole_centres = [(-20.0, -5.0), (20.0, -5.0)]

# R4: vertical-plate holes
plate_hole_diameter = 8.0
plate_hole_centres_xz = [(-18.0, 28.0), (18.0, 28.0)]

# R5: inside corner fillet
inside_fillet_radius = 4.0
inside_corner_point = (0.0, 12.0, 8.0)

# R6: centred triangular rib
rib_width_x = 6.0
rib_x_min = -3.0
rib_profile_yz = [(0.0, 8.0), (12.0, 8.0), (12.0, 20.0)]

foot = cq.Workplane("XY").box(
    foot_width_x,
    foot_depth_y,
    foot_thickness_z,
    centered=(True, True, False),
)

plate = (
    cq.Workplane(
        "XY",
        origin=(0.0, plate_y_min + plate_thickness_y / 2.0, plate_z_min),
    )
    .box(
        plate_width_x,
        plate_thickness_y,
        plate_height_z,
        centered=(True, True, False),
    )
)

bracket = foot.union(plate).clean()
bracket = bracket.edges(
    cq.NearestToPointSelector(inside_corner_point)
).fillet(inside_fillet_radius)

rib = (
    cq.Workplane("YZ", origin=(rib_x_min, 0.0, 0.0))
    .polyline(rib_profile_yz)
    .close()
    .extrude(rib_width_x)
)
bracket = bracket.union(rib).clean()

foot_holes = (
    cq.Workplane("XY")
    .pushPoints(foot_hole_centres)
    .circle(foot_hole_diameter / 2.0)
    .extrude(foot_thickness_z)
)

plate_holes = (
    cq.Workplane(
        "XZ",
        origin=(0.0, plate_y_min + plate_thickness_y, 0.0),
    )
    .pushPoints(plate_hole_centres_xz)
    .circle(plate_hole_diameter / 2.0)
    .extrude(plate_thickness_y)
)

result = bracket.cut(foot_holes).cut(plate_holes).clean()
